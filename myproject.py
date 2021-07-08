from flask import Flask, request
from flask_caching import Cache
from html import escape
import dataset
import re

app = Flask(__name__)
app.config.from_mapping({'CACHE_TYPE' : 'filesystem', 'CACHE_DIR' : 'CACHED_PAGES', 'CACHE_THRESHOLD' : 150000})
cache = Cache(app)

DB_PATH = 'sqlite:///Complete.db'
ROW_RESULT_LIMIT = 20000

page_head = """<!doctype html>
<html lang="en">
	<head>
		<meta charset="utf-8">
		<title>{{{TITLE}}}</title>
		<link rel="stylesheet" href="/static/style-v1.1.css">
		<link rel="apple-touch-icon" sizes="180x180" href="/apple-touch-icon.png">
		<link rel="icon" type="image/png" sizes="32x32" href="/favicon-32x32.png">
		<link rel="icon" type="image/png" sizes="16x16" href="/favicon-16x16.png">
		<link rel="manifest" href="/site.webmanifest">

		<!-- Global site tag (gtag.js) - Google Analytics -->
		<script async src="https://www.googletagmanager.com/gtag/js?id=UA-200755053-1">
		</script>
		<script>
			window.dataLayer = window.dataLayer || [];
			function gtag(){dataLayer.push(arguments);}
			gtag('js', new Date());

			gtag('config', 'UA-200755053-1');
		</script>
	</head>
<body>

<div class="banner"><a href="https://theprophetictimeline.com/" class="bl">The Prophetic Timeline</a><span class="sp"></span><a href="/explorer?versenumber=1" class="bl">Bible Gematria Explorer</a><span class="sp"></span><a href="https://theprophetictimeline.com/resources.html" class="bl">Resources</a><span class="sp"></span><a href="https://theprophetictimeline.com/contact.html" class="bl">Contact</a></div>

<div class="page">

"""

search_group_1 = """<table class="m_2 box clear">
	<thead>
		<tr>
			<th class="bottomline">
				<form method="GET" action="/explorer" class="autocomplete"><input type="text" class="ref_input placeh" id="input_verse_ref" name="reference" placeholder="Enter verse reference&thinsp;..." autocomplete="off"><input type="submit" class="ref_submit buttonstyle" value="Go!"></form>
			</th>
		</tr>
		<tr>
			<th class="center bcv_row">
				<form method="GET" action="/explorer"><span class="bcv_text">Book</span><input type="text" class="bcv_input" name="book" value="{{{bnum}}}" autocomplete="off"><span class="bcv_text">Chapter</span><input type="text" class="bcv_input" name="chapter" value="{{{cnum}}}" autocomplete="off"><span class="bcv_text">Verse</span><input type="text" class="bcv_input" name="verse" value="{{{vnum}}}" autocomplete="off"><input class="bcv_submit buttonstyle" type="submit" value="Go!"></form>
			</th>
		</tr>
	</thead>
</table>"""

search_group_2 = """<table class="m_2 box clear">
	<thead>
		<tr>
			<th class="bottomline same_row">
				<form method="GET" action="/strongs"><input type="text" class="same_input placeh" name="strongsnumber" placeholder="Strong's #, (G726 / H622)" autocomplete="off"><input type="submit" class="same_submit buttonstyle" value="Go!"></form>
			</th>
			<th class="bottomline same_row">
				<form method="GET" action="/gematria"><input type="text" class="same_input placeh" name="value" placeholder="Gematria search" autocomplete="off"><input type="submit" class="same_submit buttonstyle" value="Go!"></form>
			</th>
		</tr>
		<tr>
			<th class="same_row">
				<form method="GET" action="/english"><input type="text" class="same_input placeh" name="words" placeholder="Search English words..." autocomplete="off"><input type="submit" class="same_submit buttonstyle" value="Go!"></form>
			</th>
			<th class="same_row">
				<form method="GET" action="/explorer"><input type="text" class="same_input placeh" name="versenumber" placeholder="Verse number search" autocomplete="off"><input type="submit" class="same_submit buttonstyle" value="Go!"></form>
			</th>
		</tr>
	</thead>
</table>"""

page_foot = """

</div>

<div class="m_3 clear"></div>

	<script src="https://ajax.googleapis.com/ajax/libs/jquery/3.6.0/jquery.min.js"></script>
	<script src="/static/script-v1.0.js"></script>
</body>
</html>"""

#----------------------------------

# CodesHTML = '<div class="code_examples clear"><span class="codes_title">Coded Bible Verse Examples</span><br>&VeryThinSpace;&VeryThinSpace;<div class="all_codes">'
# for code in db.query('SELECT Code, ref, bnum, cnum, vnum FROM Complete WHERE Code NOTNULL'): CodesHTML += '<a href="/explorer?book=' + str(code['bnum']) + '&chapter=' + str(code['cnum']) + '&verse=' + str(code['vnum']) + '" class="codelink">' + code['ref'] + '</a><span class="c">, </span>'
# CodesHTML = CodesHTML[:-25] + '</div></div>'

CodesHTML = """<div class="code_examples clear"><span class="codes_title">Coded Bible Verse Examples</span><br>&VeryThinSpace;&VeryThinSpace;<div class="all_codes"><a href="/explorer?book=40&chapter=11&verse=12" class="codelink">Matthew 11:12</a><span class="c">, </span><a href="/explorer?book=42&chapter=6&verse=42" class="codelink">Luke 6:42</a></div></div>"""

CodesHTML2 = """<div class="code_examples clear"><span class="codes_title">Coded Bible Verse Examples</span><br>&VeryThinSpace;&VeryThinSpace;<div class="all_codes"><a href="/explorer?book=40&chapter=11&verse=12" class="codelink">Matthew 11:12</a><span class="c">, </span><a href="/explorer?book=42&chapter=6&verse=42" class="codelink">Luke 6:42</a></div><a href="https://theprophetictimeline.com/Multi_Tool.html" class="download-link">Pi Lookup Tool</a></div>"""

#----------------------------------

def remove_tags(text, front, end):
	while front in text:
		tag = front + text.split(front, 1)[1].split(end, 1)[0] + end
		text = text.replace(tag, '', 1)

	return text

def multiple_replace(string, rep_dict):
	try:
		pattern = re.compile('|'.join([re.escape(k) for k in sorted(rep_dict, key=len, reverse=True)]), flags=re.DOTALL)
		return pattern.sub(lambda x: rep_dict[x.group(0)], string)
	except:
		return string

def find_and_replace_html(search_term, html):
	if search_term == '':
		return html

	tag = False
	matching = False
	match_index = 0
	string_check = ''
	new_html = ''
	replacements = {}

	for letter in html:

		if letter == '<':
			tag = True
			if matching:
				new_html += letter
			continue

		if letter == '>':
			tag = False
			if matching:
				new_html += letter
			continue

		if not matching and not tag and letter.lower() == search_term[0].lower():
			matching = True

		if matching:
			new_html += letter

		if matching and not tag:

			if letter.lower() == search_term[match_index].lower():
				string_check += letter
				match_index += 1

				if string_check.lower() == search_term.lower():
					replacement = '<span class="green">' + new_html.replace('<i>', '</span><i><span class="green">').replace('</i>', '</span></i><span class="green">') + '</span>'

					if new_html not in replacements:
						replacements.update({new_html : replacement})

					matching = False
					match_index = 0
					string_check = ''
					new_html = ''

			else:
				matching = False
				match_index = 0
				string_check = ''
				new_html = ''

				if letter.lower() == search_term[0].lower():
					matching = True
					match_index += 1
					string_check += letter
					new_html += letter

	return multiple_replace(html, replacements)

def unhandled_e_s(transliteration):
	return transliteration.replace('ᵉ', '<span class="e_s">e</span>').replace('ˢ', '<span class="e_s">s</span>')

def Hebrew_Translit_Rules(transliteration):
	return transliteration.replace(u'\u0323', '').replace('ə', '<span class="ee">ə</span>')

def Greek_Translit_Rules(transliteration):
	return transliteration.replace('Ϛ', '<span class="other">Ϛ</span>')

def Greek_Letters_Rules(word):
	return word.replace('ϟ', '<span class="other">ϟ</span>')

def Create_Strongs_Definition(row):
	StrongsNumber = row['StrongsNumber']
	Root = row['Root']
	Value = row['Value']
	Transliteration1 = row['Transliteration1']
	Transliteration2 = row['Transliteration2']
	Transliteration = row['Transliteration']
	Part_of_Speech = row['Part_of_Speech']
	Meaning = row['Meaning']
	Strongs_Definition = row['Strongs_Definition']
	Outline = row['Outline']
	VerseCount = row['VerseCount']
	BookCount = row['BookCount']
	UsageCount = row['UsageCount']
	Note = row['Note']

	Transliteration_tag = ''
	lang_class = 'def_root_H'

	Strongs_Definition_tag = ''

	second_part = Strongs_Definition.split('<span class="def_transliteration">', 1)[1].split('</span>', 1)[1]
	first_part = Strongs_Definition.split(second_part, 1)[0]
	Strongs_Definition_tag = first_part + '<span class="main_definition">' + second_part + '</span>'
	Strongs_Definition_tag = unhandled_e_s(Strongs_Definition_tag)
	stats_tag = ''

	if StrongsNumber[:1] == 'H':
		Transliteration_tag = '<span class="translit" info="' + Transliteration2 + '">' + Hebrew_Translit_Rules(Transliteration1) + '</span>'
	else:
		Transliteration_tag = Greek_Translit_Rules(Transliteration)
		lang_class = 'def_root_G'

	if UsageCount == 0 and Note != None:
		stats_tag = Note
	else:
		verse_word = 'Verse'
		book_word = 'Book'

		if VerseCount > 1 or VerseCount == 0:
			verse_word += 's'
		if BookCount > 1 or BookCount == 0:
			book_word += 's'

		stats_tag = 'Used in ' + str(VerseCount) + ' ' + verse_word + ', ' + str(BookCount) + ' ' + book_word + ' <span class="occurrence_count">' + str(UsageCount) + '</span>&VeryThinSpace; Occurrence Count'

	return '<div><span class="' + lang_class + '">' + Root + '</span>&thinsp;, ' + Part_of_Speech + ', ' + Transliteration_tag + ' — ' + Meaning + ' <span class="value_def">(<span class="value_text">value ' + str(Value) + '</span>)</span></div><div class="line"></div>' + StrongsNumber + ', ' + Strongs_Definition_tag + '<div>' + Outline + '</div><div class="line2"></div><div class="stats">' + stats_tag + '</div>'

#----------------------------------

@cache.memoize(timeout=536112000)
def apoc(reference, APOC_previous, APOC_next):
	db = dataset.connect(DB_PATH)

	if APOC_previous == '':
		APOC_previous = '/explorer?versenumber=23145'
	else:
		APOC_previous = '/explorer?reference=' + APOC_previous.replace(' ', '+')

	if APOC_next == '':
		APOC_next = '/explorer?versenumber=23146'
	else:
		APOC_next = '/explorer?reference=' + APOC_next.replace(' ', '+')

	text = ''

	for result in db.query('SELECT * FROM APOC WHERE ref LIKE :r LIMIT 1', {'r' : '%' + reference + '%'}): text = result['text']

	page = page_head.replace('{{{TITLE}}}', 'Bible Gematria Explorer | ' + reference) + """<div class="m_1 left">
<div class="apocrypha_title">Apocrypha</div>
<div class="apoc_lines"></div>
<table class="m_2 box">
	<thead>
		<tr>
			<th class="light"><span class="arrows"><a href=""" + '"' + APOC_previous + '"' + """ class="arrow la"></a><span class="reference">""" + reference + """</span><a href=""" + '"' + APOC_next + '"' + """ class="arrow ra"></a></span><span class="av_select2" title="1611 Authorized Version">Authorized Version</span></th>
		</tr>
	</thead>
	<tbody>
		<tr>
			<td id="versedisplay">""" + text + """</td>
		</tr>
	</tbody>
</table>
</div>

<div class="m_1 left">
<div class="plain2" id="infobox">Info box. Click on an Authorized Version footnote</div>

<table class="m_2 box clear">
	<thead>
		<tr>
			<th class="apoc_padding">
				<form method="GET" action="/explorer" class="autocomplete"><input type="text" class="ref_input placeh apoc_ref" id="input_verse_ref_apoc" name="reference" placeholder="Enter verse reference&thinsp;..." autocomplete="off"><input type="submit" class="ref_submit buttonstyle" value="Go!"></form>
			</th>
		</tr>
		<tr>
			<th>
			</th>
		</tr>
	</thead>
</table>
</div>""" + page_foot

	return page



@cache.memoize(timeout=536112000)
def explorer_view(versenum, previous_versenum, next_versenum, cookie, cookie2):
	db = dataset.connect(DB_PATH)
	Complete = db['Complete']
	Strongs = db['Strongs_']

	row = Complete.find_one(id=versenum)

	Ch = row['Ch']
	ref = row['ref']
	bnum = row['bnum']
	cnum = row['cnum']
	vnum = row['vnum']
	text_1769 = row['text_1769']
	text_AV_1611 = row['text_AV_1611']
	wordnum = row['wordnum']
	letternum = row['letternum']
	total = row['total']
	KJV_Text = row['KJV_Text'].split('~')
	KJV_SN = row['KJV_SN'].split('~')
	Root_Translit = row['Root_Translit'].split('~')
	Root_Translit2 = None
	Root = row['Root'].split('~')
	Root_val = row['Root_val'].split('~')
	Original = row['Original']
	Stephanus = row['Stephanus']
	Stephanus_total = row['Stephanus_total']
	SNs_ = row['SNs_'].replace('[', '').replace(']', '').replace('(', '').replace(')', '').replace('{', '').replace('}', '').replace('~~', '~').strip('~').split('~')
	Original_Words_SN = row['Original_Words_SN'].strip('{').strip('}').strip('~').split('~')
	Original_Words_Translit = row['Original_Words_Translit'].split('~')
	Original_Words_Translit2 = None
	Original_Words = row['Original_Words'].split('~')
	Original_Words_values = row['Original_Words_values'].strip('{').strip('}').strip('~').split('~')
	LC = row['LC']
	Code = row['Code']

	if row['Root_Translit2'] != None: Root_Translit2 = row['Root_Translit2'].split('~')
	if row['Original_Words_Translit2'] != None: Original_Words_Translit2 = row['Original_Words_Translit2'].split('~')

	Code_class = 'code'

	if Code == None:
		Code = 'Code box. Any applicable codes found for this verse will be shown here.'
		Code_class = 'plain'

	alert_box = ''

	Language = ''

	Original_identifier = ' (WLC)'

	Original_Display_classes = '<td class="textright"><span class="hebrew-2">'

	manuscript_HTML = ''

	original_title = ''

	qere_tag = ''

	Table2_Translit = ''

	Greek_verses = ''

	if versenum == 6418 or versenum == 6419 or versenum == 12489:
		alert_box = '\n<div class="m_2 alert-box clear">This verse does not occur in the Leningrad Codex</div>\n'
		Original_identifier = ''

	if versenum == 25688:
		alert_box = '\n<div class="m_2 alert-box open_sans clear">This verse does not appear in the Stephanus 1550</div>\n'

	if versenum < 23146:
		Language = 'Hebrew'

		if ',' in LC:
			manuscript_HTML = '<span class="manuscript_container"><a href="/LC_/' + LC.split(',', 1)[1] + '" target="_blank" class="manuscript manuscript1"></a><a href="/LC_/' + LC.split(',', 1)[0] + '" target="_blank" class="manuscript manuscript2"></a></span>'
		else:
			manuscript_HTML = '<span class="manuscript_container"><a href="/LC_/' + LC + '" target="_blank" class="manuscript manuscript1"></a></span>'

		original_title = '<th><span class="original_title light">Original Text' + Original_identifier + '</span>' + manuscript_HTML + '</th>'

		if '<q' in row['Original_Words']:
			qere_tag = '<span class="qere_tag">View Qeres&thinsp;&thinsp;<span class="double-arrows">»</span></span>'

		Original = Original.replace('<pe ', '<span class="item_container"><pe ').replace('</pe>', '</pe></span>')
		Original = Original.replace('<samekh ', '<span class="item_container"><samekh ').replace('</samekh>', '</samekh></span>')

		Table2_Translit = ' id="Table2_Translit"'

	else:
		Language = 'Greek'

		Original_identifier = '&thinsp;&thinsp;(TR 1894)'
		Original_Display_classes = '<td id="versedisplay2"><span class="greek">'

		original_title = '<th><span class="original_title light greek_select" id="TR1894">Original Text&thinsp;&thinsp;(TR 1894)</span><span class="original_title2 light"><span class="dot dot-hide"></span><span class="greek_select" id="Stephanus1550">Stephanus 1550 <span class="small_total">(Total ' + str(Stephanus_total) + ')</span></span></span></th>'

		Stephanus = Greek_Letters_Rules(Stephanus)
		Greek_verses = '\n\n<div id="TR1894_verse" hidden><span class="greek">' + Original + '</span></div>\n<div id="Stephanus_verse" hidden><span class="greek">' + Stephanus + '</span></div>'

	totaldisplay_class = ''

	if total >= 10000:
		totaldisplay_class = 'class="totaldisplay" '

	All_StrongsNumbers = []

	for number in KJV_SN + SNs_ + Original_Words_SN:
		if number != 'NONE' and number not in All_StrongsNumbers:
			All_StrongsNumbers.append(number)

	results = Strongs.find(StrongsNumber=All_StrongsNumbers)
	AllStrongsNumbersHTML = ''

	for result in results:
		AllStrongsNumbersHTML += '<div id="' + result['StrongsNumber'] + '" hidden>' + Create_Strongs_Definition(result) + '</div>\n'

	AllStrongsNumbersHTML = AllStrongsNumbersHTML[:-1]

	Roots_Table = ''

	if Language == 'Hebrew':

		for KJV_Text_, KJV_SN_, Root_Translit_, Root_Translit2_, Root_, Root_val_ in zip(KJV_Text, KJV_SN, Root_Translit, Root_Translit2, Root, Root_val):
			SN_Width_tag = ' s-' + str(len(KJV_SN_) - 1)

			Roots_Table += '		<tr>\n'
			Roots_Table += '			<td>' + KJV_Text_.replace('<s ', '<st ').replace('</s>', '</st>') + '</td>\n'
			Roots_Table += '			<td><span class="strongs' + SN_Width_tag + '" data="' + KJV_SN_ + '">' + KJV_SN_ + '</span><span class="translit" info="' + Root_Translit2_ + '">' + Hebrew_Translit_Rules(Root_Translit_) + '</span></td>\n'
			Roots_Table += '			<td class="assistant">' + Root_ + '</td>\n'
			Roots_Table += '			<td>' + Root_val_ + '</td>\n'
			Roots_Table += '		</tr>\n'

	else:

		for KJV_Text_, KJV_SN_, Root_Translit_, Root_, Root_val_ in zip(KJV_Text, KJV_SN, Root_Translit, Root, Root_val):
			SN_Width_tag = ' s-' + str(len(KJV_SN_) - 1)

			Roots_Table += '		<tr>\n'
			Roots_Table += '			<td>' + KJV_Text_.replace('<s ', '<st ').replace('</s>', '</st>') + '</td>\n'
			Roots_Table += '			<td><span class="strongs' + SN_Width_tag + '" data="' + KJV_SN_ + '">' + KJV_SN_ + '</span><span class="translit">' + Greek_Translit_Rules(Root_Translit_) + '</span></td>\n'
			Roots_Table += '			<td class="greek">' + Root_ + '</td>\n'
			Roots_Table += '			<td>' + Root_val_ + '</td>\n'
			Roots_Table += '		</tr>\n'

	Roots_Table = Roots_Table[:-1]

	Words_Table = ''

	row_n = 1

	if Language == 'Hebrew':

		for Original_Words_SN_, Original_Words_Translit_, Original_Words_Translit2_, Original_Words_, Original_Words_values_ in zip(Original_Words_SN, Original_Words_Translit, Original_Words_Translit2, Original_Words, Original_Words_values):
			SN_Width_tag = ' s-' + str(len(Original_Words_SN_) - 1)

			SN_HTML = '<span class="strongs' + SN_Width_tag + '" data="' + Original_Words_SN_ + '">' + Original_Words_SN_ + '</span>'
			is_none = ''

			if Original_Words_SN_ == 'NONE':
				SN_HTML = '<span class="none-dash"></span>'
				is_none = ' class="center"'

			if 'asn=' in Original_Words_:
				asn = Original_Words_.split('asn="', 1)[1].split('"', 1)[0]
				SN_Width_tag_asn = ' s-' + str(len(asn) - 1)

				SN_HTML += ' <span class="asn' + SN_Width_tag_asn + '" data="' + asn + '">' + asn + '</span>'

			if 'gsn=' in Original_Words_:
				gsn = Original_Words_.split('gsn="', 1)[1].split('"', 1)[0]
				parts = Original_Words_.split('parts="', 1)[1].split('"', 1)[0]
				SN_Width_tag_gsn = ' s-' + str(len(gsn) - 1)

				SN_HTML += ' <span class="gsn' + SN_Width_tag_gsn + '" data="' + gsn + '" parts="' + parts + '">' + gsn + '</span>'

			if Original_Words_values_ == 'NONE': Original_Words_values_ = ''

			is_qere = ''

			checkbox_HTML = '<span class="checkcontainer"><input type="checkbox" id="box-' + str(row_n) + '" class="wordval" value="' + Original_Words_values_ + '" autocomplete="off" checked><label for="box-' + str(row_n) + '"></label></span>'

			Translit_HTML = '<span class="translit" info="' + Original_Words_Translit2_ + '">' + Hebrew_Translit_Rules(Original_Words_Translit_) + '</span>'

			if Original_Words_Translit_ == 'NONE':		# Reversed nun
				Translit_HTML = ''
				Original = Original.replace('<reversednun ', '<span class="item_container"><reversednun class="reversednun" ').replace('</reversednun>', '</reversednun></span>')
				Original_Words_ = Original_Words_.replace('<reversednun ', '<span class="item_container"><reversednun ').replace('</reversednun>', '</reversednun></span>')

				SN_HTML = ''
				is_none = ''

			if '<q' in Original_Words_:
				Original_Words_ = Original_Words_.replace('<q', '<qere').replace('</q>', '</qere>')
				is_qere = ' class="qere"'
				checkbox_HTML = ''

			Words_Table += '		<tr' + is_qere + '>\n'
			Words_Table += '			<td' + is_none + '>' + SN_HTML + '</td>\n'
			Words_Table += '			<td>' + Translit_HTML + '</td>\n'
			Words_Table += '			<td class="hebrew">' + Original_Words_.replace('</esv><esv', '</esv>&nbsp;<esv').replace('<esv', '<span class="item_container"><esv').replace('</esv>', '</esv></span>') + '</td>\n'
			Words_Table += '			<td>' + Original_Words_values_ + '</td>\n'
			Words_Table += '			<td>' + checkbox_HTML + '</td>\n'
			Words_Table += '		</tr>\n'

			row_n += 1

	else:

		for Original_Words_SN_, Original_Words_Translit_, Original_Words_, Original_Words_values_ in zip(Original_Words_SN, Original_Words_Translit, Original_Words, Original_Words_values):
			SN_Width_tag = ' s-' + str(len(Original_Words_SN_) - 1)

			SN_HTML = '<span class="strongs' + SN_Width_tag + '" data="' + Original_Words_SN_ + '">' + Original_Words_SN_ + '</span>'
			is_none = ''

			if Original_Words_SN_ == 'NONE':
				SN_HTML = '<span class="none-dash"></span>'
				is_none = ' class="center"'

			if 'asn=' in Original_Words_:
				asn = Original_Words_.split('asn="', 1)[1].split('"', 1)[0]
				SN_Width_tag_asn = ' s-' + str(len(asn) - 1)

				SN_HTML += ' <span class="asn' + SN_Width_tag_asn + '" data="' + asn + '">' + asn + '</span>'

			if 'gsn=' in Original_Words_:
				gsn_tag = Original_Words_.split('gsn="', 1)[1].split('"', 1)[0]
				gsn = gsn_tag.split(',', 1)[0]
				parts = gsn_tag.split(',', 1)[1]
				SN_Width_tag_gsn = ' s-' + str(len(gsn) - 1)

				SN_HTML += ' <span class="gsn2' + SN_Width_tag_gsn + '" data="' + gsn + '" parts="' + parts + '">' + gsn + '</span>'

			if 'AddStrongs=' in Original_Words_:
				AddStrongs = Original_Words_.split('AddStrongs="', 1)[1].split('"', 1)[0]

				for item in AddStrongs.split('|'):
					addsn = item.split('`')[0]
					SN_Width_tag_addsn = ' s-' + str(len(addsn) - 1)

					SN_HTML += ' <span class="addsn' + SN_Width_tag_addsn + '" data="' + addsn + '">' + addsn + '</span>'

			Words_Table += '		<tr>\n'
			Words_Table += '			<td' + is_none + '>' + SN_HTML + '</td>\n'
			Words_Table += '			<td><span class="translit">' + Original_Words_Translit_ + '</span></td>\n'
			Words_Table += '			<td class="greek">' + Original_Words_.replace('<w', '<span class="item_container"><gw').replace('</w>', '</gw></span>') + '</td>\n'
			Words_Table += '			<td>' + Original_Words_values_ + '</td>\n'
			Words_Table += '			<td><span class="checkcontainer"><input type="checkbox" id="box-' + str(row_n) + '" class="wordval" value="' + Original_Words_values_ + '" autocomplete="off" checked><label for="box-' + str(row_n) + '"></label></span></td>\n'
			Words_Table += '		</tr>\n'

			row_n += 1

	Words_Table = Words_Table[:-1]

	kjv_select_class = 'class="regular" '
	av_select_class = 'class="regular" '

	versedisplay_text = ''
	versedisplay2_text = Original

	if cookie == 'kjv_select':
		av_select_class = ''
		versedisplay_text = text_1769

	elif cookie == 'av_select':
		kjv_select_class = ''
		versedisplay_text = text_AV_1611

	if cookie2 == 'Stephanus1550' and Language == 'Greek':
		versedisplay2_text = Stephanus
		original_title = original_title.replace('dot dot-hide', 'dot')

	page = page_head.replace('{{{TITLE}}}', 'Bible Gematria Explorer | ' + ref) + """<div id="KJV_verse" hidden>""" + text_1769 + """</div>
<div id="av_verse" hidden>""" + text_AV_1611 + '</div>' + Greek_verses + """

""" + AllStrongsNumbersHTML + """

<div class="m_1 left">
<table class="m_2 box">
	<thead>
		<tr>
			<th class="light"><span class="arrows"><a href="/explorer?versenumber=""" + str(previous_versenum) + '"' + """ class="arrow la"></a><span class="reference">""" + ref + """</span><a href="/explorer?versenumber=""" + str(next_versenum) + '"' + """ class="arrow ra"></a></span><span """ + kjv_select_class + """id="kjv_select">Modern KJV</span><span class="dash">—</span><span """ + av_select_class + """id="av_select" title="1611 Authorized Version">Authorized Version</span></th>
		</tr>
	</thead>
	<tbody>
		<tr>
			<td id="versedisplay">""" + versedisplay_text + """</td>
		</tr>
	</tbody>
</table>

<table class="m_2 box clear">
	<thead>
		<tr>
			""" + original_title + """
		</tr>
	</thead>
	<tbody>
		<tr>
			""" + Original_Display_classes + versedisplay2_text + """</span></td>
		</tr>
	</tbody>
</table>
""" + alert_box + """
<table class="m_2 clear t1 Table1">
	<thead>
		<tr>
			<th colspan="4"><span id="verse_info">Verse #""" + str(versenum) + """ (Ch. #""" + str(Ch) + """) — <span class="light">""" + str(wordnum) + """ words, """ + str(letternum) + """ letters</span></span><span id="clipboard" class="clipboard clipboard1" title="Copy verse info to clipboard"><span class="clipboard clipboard2"></span><span class="copied">Text Copied!</span></span></th>
		</tr>
		<tr>
			<th class="fill" colspan="4">Data from Strong's Concordance</th>
		</tr>
		<tr>
			<th>KJV</th>
			<th>Strong's #</th>
			<th>""" + Language + """</th>
			<th>Value</th>
		</tr>
	</thead>
	<tbody class="t2">
""" + Roots_Table + """
	</tbody>
</table>

<table class="m_3 t1 Table2">
	<thead>
		<tr>
			<th colspan="3" class="light textright">Total =</th>
			<th colspan="2" class="textright"><span """ + totaldisplay_class + 'id="totaldisplay">' + str(total) + '</span><span class="item_container"><span class="checkcontainer check_margin"><input type="checkbox" id="total" value="' + str(total) + '" autocomplete="off" checked><label for="total"></label></span>' + qere_tag + """</span></th>
		</tr>
		<tr>
			<th class="fill" colspan="5">Original Text</th>
		</tr>
		<tr>
			<th>Strong's #</th>
			<th""" + Table2_Translit + """>Translit</th>
			<th>""" + Language + """</th>
			<th>Value</th>
			<th>Inc</th>
		</tr>
	</thead>
	<tbody class="t2">
""" + Words_Table + """
	</tbody>
</table>
</div>

<div class="m_1 left">
<div class="plain2" id="infobox">Info box. Click on a Strong's # link, or Authorized Version footnote</div>

""" + search_group_1.replace('{{{bnum}}}', str(bnum)).replace('{{{cnum}}}', str(cnum)).replace('{{{vnum}}}', str(vnum)) + '\n\n' + search_group_2 + """

<div class=""" + '"' + Code_class + """ clear" id="codebox">""" + Code + """</div>

""" + CodesHTML2 + """
</div>""" + page_foot

	return page



@app.route('/explorer', methods=['GET'])
def explorer():
	versenum = request.args.get('versenumber')
	book = request.args.get('book')
	chapter = request.args.get('chapter')
	verse = request.args.get('verse')
	reference = request.args.get('reference')

	# ---------------------------------------------------

	the_books_lower = ['genesis', 'exodus', 'leviticus', 'numbers', 'deuteronomy', 'joshua', 'judges', 'ruth', '1 samuel', '2 samuel', '1 kings', '2 kings', '1 chronicles', '2 chronicles', 'ezra', 'nehemiah', 'esther', 'job', 'psalm', 'proverbs', 'ecclesiastes', 'song of solomon', 'isaiah', 'jeremiah', 'lamentations', 'ezekiel', 'daniel', 'hosea', 'joel', 'amos', 'obadiah', 'jonah', 'micah', 'nahum', 'habakkuk', 'zephaniah', 'haggai', 'zechariah', 'malachi', 'matthew', 'mark', 'luke', 'john', 'acts', 'romans', '1 corinthians', '2 corinthians', 'galatians', 'ephesians', 'philippians', 'colossians', '1 thessalonians', '2 thessalonians', '1 timothy', '2 timothy', 'titus', 'philemon', 'hebrews', 'james', '1 peter', '2 peter', '1 john', '2 john', '3 john', 'jude', 'revelation', '1 esdras', '2 esdras', 'tobit', 'judith', 'additions to esther', 'wisdom of solomon', 'ecclesiasticus', 'baruch', 'prayer of azariah', 'susanna', 'bel and the dragon', 'prayer of manasseh', '1 maccabees', '2 maccabees']
	the_books = ['Genesis', 'Exodus', 'Leviticus', 'Numbers', 'Deuteronomy', 'Joshua', 'Judges', 'Ruth', '1 Samuel', '2 Samuel', '1 Kings', '2 Kings', '1 Chronicles', '2 Chronicles', 'Ezra', 'Nehemiah', 'Esther', 'Job', 'Psalm', 'Proverbs', 'Ecclesiastes', 'Song of Solomon', 'Isaiah', 'Jeremiah', 'Lamentations', 'Ezekiel', 'Daniel', 'Hosea', 'Joel', 'Amos', 'Obadiah', 'Jonah', 'Micah', 'Nahum', 'Habakkuk', 'Zephaniah', 'Haggai', 'Zechariah', 'Malachi', 'Matthew', 'Mark', 'Luke', 'John', 'Acts', 'Romans', '1 Corinthians', '2 Corinthians', 'Galatians', 'Ephesians', 'Philippians', 'Colossians', '1 Thessalonians', '2 Thessalonians', '1 Timothy', '2 Timothy', 'Titus', 'Philemon', 'Hebrews', 'James', '1 Peter', '2 Peter', '1 John', '2 John', '3 John', 'Jude', 'Revelation', '1 Esdras', '2 Esdras', 'Tobit', 'Judith', 'Additions to Esther', 'Wisdom of Solomon', 'Ecclesiasticus', 'Baruch', 'Prayer of Azariah', 'Susanna', 'Bel and the Dragon', 'Prayer of Manasseh', '1 Maccabees', '2 Maccabees']
	the_refs = {'Genesis' : [50, {1 : 31, 2 : 25, 3 : 24, 4 : 26, 5 : 32, 6 : 22, 7 : 24, 8 : 22, 9 : 29, 10 : 32, 11 : 32, 12 : 20, 13 : 18, 14 : 24, 15 : 21, 16 : 16, 17 : 27, 18 : 33, 19 : 38, 20 : 18, 21 : 34, 22 : 24, 23 : 20, 24 : 67, 25 : 34, 26 : 35, 27 : 46, 28 : 22, 29 : 35, 30 : 43, 31 : 55, 32 : 32, 33 : 20, 34 : 31, 35 : 29, 36 : 43, 37 : 36, 38 : 30, 39 : 23, 40 : 23, 41 : 57, 42 : 38, 43 : 34, 44 : 34, 45 : 28, 46 : 34, 47 : 31, 48 : 22, 49 : 33, 50 : 26}], 'Exodus' : [40, {1 : 22, 2 : 25, 3 : 22, 4 : 31, 5 : 23, 6 : 30, 7 : 25, 8 : 32, 9 : 35, 10 : 29, 11 : 10, 12 : 51, 13 : 22, 14 : 31, 15 : 27, 16 : 36, 17 : 16, 18 : 27, 19 : 25, 20 : 26, 21 : 36, 22 : 31, 23 : 33, 24 : 18, 25 : 40, 26 : 37, 27 : 21, 28 : 43, 29 : 46, 30 : 38, 31 : 18, 32 : 35, 33 : 23, 34 : 35, 35 : 35, 36 : 38, 37 : 29, 38 : 31, 39 : 43, 40 : 38}], 'Leviticus' : [27, {1 : 17, 2 : 16, 3 : 17, 4 : 35, 5 : 19, 6 : 30, 7 : 38, 8 : 36, 9 : 24, 10 : 20, 11 : 47, 12 : 8, 13 : 59, 14 : 57, 15 : 33, 16 : 34, 17 : 16, 18 : 30, 19 : 37, 20 : 27, 21 : 24, 22 : 33, 23 : 44, 24 : 23, 25 : 55, 26 : 46, 27 : 34}], 'Numbers' : [36, {1 : 54, 2 : 34, 3 : 51, 4 : 49, 5 : 31, 6 : 27, 7 : 89, 8 : 26, 9 : 23, 10 : 36, 11 : 35, 12 : 16, 13 : 33, 14 : 45, 15 : 41, 16 : 50, 17 : 13, 18 : 32, 19 : 22, 20 : 29, 21 : 35, 22 : 41, 23 : 30, 24 : 25, 25 : 18, 26 : 65, 27 : 23, 28 : 31, 29 : 40, 30 : 16, 31 : 54, 32 : 42, 33 : 56, 34 : 29, 35 : 34, 36 : 13}], 'Deuteronomy' : [34, {1 : 46, 2 : 37, 3 : 29, 4 : 49, 5 : 33, 6 : 25, 7 : 26, 8 : 20, 9 : 29, 10 : 22, 11 : 32, 12 : 32, 13 : 18, 14 : 29, 15 : 23, 16 : 22, 17 : 20, 18 : 22, 19 : 21, 20 : 20, 21 : 23, 22 : 30, 23 : 25, 24 : 22, 25 : 19, 26 : 19, 27 : 26, 28 : 68, 29 : 29, 30 : 20, 31 : 30, 32 : 52, 33 : 29, 34 : 12}], 'Joshua' : [24, {1 : 18, 2 : 24, 3 : 17, 4 : 24, 5 : 15, 6 : 27, 7 : 26, 8 : 35, 9 : 27, 10 : 43, 11 : 23, 12 : 24, 13 : 33, 14 : 15, 15 : 63, 16 : 10, 17 : 18, 18 : 28, 19 : 51, 20 : 9, 21 : 45, 22 : 34, 23 : 16, 24 : 33}], 'Judges' : [21, {1 : 36, 2 : 23, 3 : 31, 4 : 24, 5 : 31, 6 : 40, 7 : 25, 8 : 35, 9 : 57, 10 : 18, 11 : 40, 12 : 15, 13 : 25, 14 : 20, 15 : 20, 16 : 31, 17 : 13, 18 : 31, 19 : 30, 20 : 48, 21 : 25}], 'Ruth' : [4, {1 : 22, 2 : 23, 3 : 18, 4 : 22}], '1 Samuel' : [31, {1 : 28, 2 : 36, 3 : 21, 4 : 22, 5 : 12, 6 : 21, 7 : 17, 8 : 22, 9 : 27, 10 : 27, 11 : 15, 12 : 25, 13 : 23, 14 : 52, 15 : 35, 16 : 23, 17 : 58, 18 : 30, 19 : 24, 20 : 42, 21 : 15, 22 : 23, 23 : 29, 24 : 22, 25 : 44, 26 : 25, 27 : 12, 28 : 25, 29 : 11, 30 : 31, 31 : 13}], '2 Samuel' : [24, {1 : 27, 2 : 32, 3 : 39, 4 : 12, 5 : 25, 6 : 23, 7 : 29, 8 : 18, 9 : 13, 10 : 19, 11 : 27, 12 : 31, 13 : 39, 14 : 33, 15 : 37, 16 : 23, 17 : 29, 18 : 33, 19 : 43, 20 : 26, 21 : 22, 22 : 51, 23 : 39, 24 : 25}], '1 Kings' : [22, {1 : 53, 2 : 46, 3 : 28, 4 : 34, 5 : 18, 6 : 38, 7 : 51, 8 : 66, 9 : 28, 10 : 29, 11 : 43, 12 : 33, 13 : 34, 14 : 31, 15 : 34, 16 : 34, 17 : 24, 18 : 46, 19 : 21, 20 : 43, 21 : 29, 22 : 53}], '2 Kings' : [25, {1 : 18, 2 : 25, 3 : 27, 4 : 44, 5 : 27, 6 : 33, 7 : 20, 8 : 29, 9 : 37, 10 : 36, 11 : 21, 12 : 21, 13 : 25, 14 : 29, 15 : 38, 16 : 20, 17 : 41, 18 : 37, 19 : 37, 20 : 21, 21 : 26, 22 : 20, 23 : 37, 24 : 20, 25 : 30}], '1 Chronicles' : [29, {1 : 54, 2 : 55, 3 : 24, 4 : 43, 5 : 26, 6 : 81, 7 : 40, 8 : 40, 9 : 44, 10 : 14, 11 : 47, 12 : 40, 13 : 14, 14 : 17, 15 : 29, 16 : 43, 17 : 27, 18 : 17, 19 : 19, 20 : 8, 21 : 30, 22 : 19, 23 : 32, 24 : 31, 25 : 31, 26 : 32, 27 : 34, 28 : 21, 29 : 30}], '2 Chronicles' : [36, {1 : 17, 2 : 18, 3 : 17, 4 : 22, 5 : 14, 6 : 42, 7 : 22, 8 : 18, 9 : 31, 10 : 19, 11 : 23, 12 : 16, 13 : 22, 14 : 15, 15 : 19, 16 : 14, 17 : 19, 18 : 34, 19 : 11, 20 : 37, 21 : 20, 22 : 12, 23 : 21, 24 : 27, 25 : 28, 26 : 23, 27 : 9, 28 : 27, 29 : 36, 30 : 27, 31 : 21, 32 : 33, 33 : 25, 34 : 33, 35 : 27, 36 : 23}], 'Ezra' : [10, {1 : 11, 2 : 70, 3 : 13, 4 : 24, 5 : 17, 6 : 22, 7 : 28, 8 : 36, 9 : 15, 10 : 44}], 'Nehemiah' : [13, {1 : 11, 2 : 20, 3 : 32, 4 : 23, 5 : 19, 6 : 19, 7 : 73, 8 : 18, 9 : 38, 10 : 39, 11 : 36, 12 : 47, 13 : 31}], 'Esther' : [10, {1 : 22, 2 : 23, 3 : 15, 4 : 17, 5 : 14, 6 : 14, 7 : 10, 8 : 17, 9 : 32, 10 : 3}], 'Job' : [42, {1 : 22, 2 : 13, 3 : 26, 4 : 21, 5 : 27, 6 : 30, 7 : 21, 8 : 22, 9 : 35, 10 : 22, 11 : 20, 12 : 25, 13 : 28, 14 : 22, 15 : 35, 16 : 22, 17 : 16, 18 : 21, 19 : 29, 20 : 29, 21 : 34, 22 : 30, 23 : 17, 24 : 25, 25 : 6, 26 : 14, 27 : 23, 28 : 28, 29 : 25, 30 : 31, 31 : 40, 32 : 22, 33 : 33, 34 : 37, 35 : 16, 36 : 33, 37 : 24, 38 : 41, 39 : 30, 40 : 24, 41 : 34, 42 : 17}], 'Psalm' : [150, {1 : 6, 2 : 12, 3 : 8, 4 : 8, 5 : 12, 6 : 10, 7 : 17, 8 : 9, 9 : 20, 10 : 18, 11 : 7, 12 : 8, 13 : 6, 14 : 7, 15 : 5, 16 : 11, 17 : 15, 18 : 50, 19 : 14, 20 : 9, 21 : 13, 22 : 31, 23 : 6, 24 : 10, 25 : 22, 26 : 12, 27 : 14, 28 : 9, 29 : 11, 30 : 12, 31 : 24, 32 : 11, 33 : 22, 34 : 22, 35 : 28, 36 : 12, 37 : 40, 38 : 22, 39 : 13, 40 : 17, 41 : 13, 42 : 11, 43 : 5, 44 : 26, 45 : 17, 46 : 11, 47 : 9, 48 : 14, 49 : 20, 50 : 23, 51 : 19, 52 : 9, 53 : 6, 54 : 7, 55 : 23, 56 : 13, 57 : 11, 58 : 11, 59 : 17, 60 : 12, 61 : 8, 62 : 12, 63 : 11, 64 : 10, 65 : 13, 66 : 20, 67 : 7, 68 : 35, 69 : 36, 70 : 5, 71 : 24, 72 : 20, 73 : 28, 74 : 23, 75 : 10, 76 : 12, 77 : 20, 78 : 72, 79 : 13, 80 : 19, 81 : 16, 82 : 8, 83 : 18, 84 : 12, 85 : 13, 86 : 17, 87 : 7, 88 : 18, 89 : 52, 90 : 17, 91 : 16, 92 : 15, 93 : 5, 94 : 23, 95 : 11, 96 : 13, 97 : 12, 98 : 9, 99 : 9, 100 : 5, 101 : 8, 102 : 28, 103 : 22, 104 : 35, 105 : 45, 106 : 48, 107 : 43, 108 : 13, 109 : 31, 110 : 7, 111 : 10, 112 : 10, 113 : 9, 114 : 8, 115 : 18, 116 : 19, 117 : 2, 118 : 29, 119 : 176, 120 : 7, 121 : 8, 122 : 9, 123 : 4, 124 : 8, 125 : 5, 126 : 6, 127 : 5, 128 : 6, 129 : 8, 130 : 8, 131 : 3, 132 : 18, 133 : 3, 134 : 3, 135 : 21, 136 : 26, 137 : 9, 138 : 8, 139 : 24, 140 : 13, 141 : 10, 142 : 7, 143 : 12, 144 : 15, 145 : 21, 146 : 10, 147 : 20, 148 : 14, 149 : 9, 150 : 6}], 'Proverbs' : [31, {1 : 33, 2 : 22, 3 : 35, 4 : 27, 5 : 23, 6 : 35, 7 : 27, 8 : 36, 9 : 18, 10 : 32, 11 : 31, 12 : 28, 13 : 25, 14 : 35, 15 : 33, 16 : 33, 17 : 28, 18 : 24, 19 : 29, 20 : 30, 21 : 31, 22 : 29, 23 : 35, 24 : 34, 25 : 28, 26 : 28, 27 : 27, 28 : 28, 29 : 27, 30 : 33, 31 : 31}], 'Ecclesiastes' : [12, {1 : 18, 2 : 26, 3 : 22, 4 : 16, 5 : 20, 6 : 12, 7 : 29, 8 : 17, 9 : 18, 10 : 20, 11 : 10, 12 : 14}], 'Song of Solomon' : [8, {1 : 17, 2 : 17, 3 : 11, 4 : 16, 5 : 16, 6 : 13, 7 : 13, 8 : 14}], 'Isaiah' : [66, {1 : 31, 2 : 22, 3 : 26, 4 : 6, 5 : 30, 6 : 13, 7 : 25, 8 : 22, 9 : 21, 10 : 34, 11 : 16, 12 : 6, 13 : 22, 14 : 32, 15 : 9, 16 : 14, 17 : 14, 18 : 7, 19 : 25, 20 : 6, 21 : 17, 22 : 25, 23 : 18, 24 : 23, 25 : 12, 26 : 21, 27 : 13, 28 : 29, 29 : 24, 30 : 33, 31 : 9, 32 : 20, 33 : 24, 34 : 17, 35 : 10, 36 : 22, 37 : 38, 38 : 22, 39 : 8, 40 : 31, 41 : 29, 42 : 25, 43 : 28, 44 : 28, 45 : 25, 46 : 13, 47 : 15, 48 : 22, 49 : 26, 50 : 11, 51 : 23, 52 : 15, 53 : 12, 54 : 17, 55 : 13, 56 : 12, 57 : 21, 58 : 14, 59 : 21, 60 : 22, 61 : 11, 62 : 12, 63 : 19, 64 : 12, 65 : 25, 66 : 24}], 'Jeremiah' : [52, {1 : 19, 2 : 37, 3 : 25, 4 : 31, 5 : 31, 6 : 30, 7 : 34, 8 : 22, 9 : 26, 10 : 25, 11 : 23, 12 : 17, 13 : 27, 14 : 22, 15 : 21, 16 : 21, 17 : 27, 18 : 23, 19 : 15, 20 : 18, 21 : 14, 22 : 30, 23 : 40, 24 : 10, 25 : 38, 26 : 24, 27 : 22, 28 : 17, 29 : 32, 30 : 24, 31 : 40, 32 : 44, 33 : 26, 34 : 22, 35 : 19, 36 : 32, 37 : 21, 38 : 28, 39 : 18, 40 : 16, 41 : 18, 42 : 22, 43 : 13, 44 : 30, 45 : 5, 46 : 28, 47 : 7, 48 : 47, 49 : 39, 50 : 46, 51 : 64, 52 : 34}], 'Lamentations' : [5, {1 : 22, 2 : 22, 3 : 66, 4 : 22, 5 : 22}], 'Ezekiel' : [48, {1 : 28, 2 : 10, 3 : 27, 4 : 17, 5 : 17, 6 : 14, 7 : 27, 8 : 18, 9 : 11, 10 : 22, 11 : 25, 12 : 28, 13 : 23, 14 : 23, 15 : 8, 16 : 63, 17 : 24, 18 : 32, 19 : 14, 20 : 49, 21 : 32, 22 : 31, 23 : 49, 24 : 27, 25 : 17, 26 : 21, 27 : 36, 28 : 26, 29 : 21, 30 : 26, 31 : 18, 32 : 32, 33 : 33, 34 : 31, 35 : 15, 36 : 38, 37 : 28, 38 : 23, 39 : 29, 40 : 49, 41 : 26, 42 : 20, 43 : 27, 44 : 31, 45 : 25, 46 : 24, 47 : 23, 48 : 35}], 'Daniel' : [12, {1 : 21, 2 : 49, 3 : 30, 4 : 37, 5 : 31, 6 : 28, 7 : 28, 8 : 27, 9 : 27, 10 : 21, 11 : 45, 12 : 13}], 'Hosea' : [14, {1 : 11, 2 : 23, 3 : 5, 4 : 19, 5 : 15, 6 : 11, 7 : 16, 8 : 14, 9 : 17, 10 : 15, 11 : 12, 12 : 14, 13 : 16, 14 : 9}], 'Joel' : [3, {1 : 20, 2 : 32, 3 : 21}], 'Amos' : [9, {1 : 15, 2 : 16, 3 : 15, 4 : 13, 5 : 27, 6 : 14, 7 : 17, 8 : 14, 9 : 15}], 'Obadiah' : [1, {1 : 21}], 'Jonah' : [4, {1 : 17, 2 : 10, 3 : 10, 4 : 11}], 'Micah' : [7, {1 : 16, 2 : 13, 3 : 12, 4 : 13, 5 : 15, 6 : 16, 7 : 20}], 'Nahum' : [3, {1 : 15, 2 : 13, 3 : 19}], 'Habakkuk' : [3, {1 : 17, 2 : 20, 3 : 19}], 'Zephaniah' : [3, {1 : 18, 2 : 15, 3 : 20}], 'Haggai' : [2, {1 : 15, 2 : 23}], 'Zechariah' : [14, {1 : 21, 2 : 13, 3 : 10, 4 : 14, 5 : 11, 6 : 15, 7 : 14, 8 : 23, 9 : 17, 10 : 12, 11 : 17, 12 : 14, 13 : 9, 14 : 21}], 'Malachi' : [4, {1 : 14, 2 : 17, 3 : 18, 4 : 6}], 'Matthew' : [28, {1 : 25, 2 : 23, 3 : 17, 4 : 25, 5 : 48, 6 : 34, 7 : 29, 8 : 34, 9 : 38, 10 : 42, 11 : 30, 12 : 50, 13 : 58, 14 : 36, 15 : 39, 16 : 28, 17 : 27, 18 : 35, 19 : 30, 20 : 34, 21 : 46, 22 : 46, 23 : 39, 24 : 51, 25 : 46, 26 : 75, 27 : 66, 28 : 20}], 'Mark' : [16, {1 : 45, 2 : 28, 3 : 35, 4 : 41, 5 : 43, 6 : 56, 7 : 37, 8 : 38, 9 : 50, 10 : 52, 11 : 33, 12 : 44, 13 : 37, 14 : 72, 15 : 47, 16 : 20}], 'Luke' : [24, {1 : 80, 2 : 52, 3 : 38, 4 : 44, 5 : 39, 6 : 49, 7 : 50, 8 : 56, 9 : 62, 10 : 42, 11 : 54, 12 : 59, 13 : 35, 14 : 35, 15 : 32, 16 : 31, 17 : 37, 18 : 43, 19 : 48, 20 : 47, 21 : 38, 22 : 71, 23 : 56, 24 : 53}], 'John' : [21, {1 : 51, 2 : 25, 3 : 36, 4 : 54, 5 : 47, 6 : 71, 7 : 53, 8 : 59, 9 : 41, 10 : 42, 11 : 57, 12 : 50, 13 : 38, 14 : 31, 15 : 27, 16 : 33, 17 : 26, 18 : 40, 19 : 42, 20 : 31, 21 : 25}], 'Acts' : [28, {1 : 26, 2 : 47, 3 : 26, 4 : 37, 5 : 42, 6 : 15, 7 : 60, 8 : 40, 9 : 43, 10 : 48, 11 : 30, 12 : 25, 13 : 52, 14 : 28, 15 : 41, 16 : 40, 17 : 34, 18 : 28, 19 : 41, 20 : 38, 21 : 40, 22 : 30, 23 : 35, 24 : 27, 25 : 27, 26 : 32, 27 : 44, 28 : 31}], 'Romans' : [16, {1 : 32, 2 : 29, 3 : 31, 4 : 25, 5 : 21, 6 : 23, 7 : 25, 8 : 39, 9 : 33, 10 : 21, 11 : 36, 12 : 21, 13 : 14, 14 : 23, 15 : 33, 16 : 27}], '1 Corinthians' : [16, {1 : 31, 2 : 16, 3 : 23, 4 : 21, 5 : 13, 6 : 20, 7 : 40, 8 : 13, 9 : 27, 10 : 33, 11 : 34, 12 : 31, 13 : 13, 14 : 40, 15 : 58, 16 : 24}], '2 Corinthians' : [13, {1 : 24, 2 : 17, 3 : 18, 4 : 18, 5 : 21, 6 : 18, 7 : 16, 8 : 24, 9 : 15, 10 : 18, 11 : 33, 12 : 21, 13 : 14}], 'Galatians' : [6, {1 : 24, 2 : 21, 3 : 29, 4 : 31, 5 : 26, 6 : 18}], 'Ephesians' : [6, {1 : 23, 2 : 22, 3 : 21, 4 : 32, 5 : 33, 6 : 24}], 'Philippians' : [4, {1 : 30, 2 : 30, 3 : 21, 4 : 23}], 'Colossians' : [4, {1 : 29, 2 : 23, 3 : 25, 4 : 18}], '1 Thessalonians' : [5, {1 : 10, 2 : 20, 3 : 13, 4 : 18, 5 : 28}], '2 Thessalonians' : [3, {1 : 12, 2 : 17, 3 : 18}], '1 Timothy' : [6, {1 : 20, 2 : 15, 3 : 16, 4 : 16, 5 : 25, 6 : 21}], '2 Timothy' : [4, {1 : 18, 2 : 26, 3 : 17, 4 : 22}], 'Titus' : [3, {1 : 16, 2 : 15, 3 : 15}], 'Philemon' : [1, {1 : 25}], 'Hebrews' : [13, {1 : 14, 2 : 18, 3 : 19, 4 : 16, 5 : 14, 6 : 20, 7 : 28, 8 : 13, 9 : 28, 10 : 39, 11 : 40, 12 : 29, 13 : 25}], 'James' : [5, {1 : 27, 2 : 26, 3 : 18, 4 : 17, 5 : 20}], '1 Peter' : [5, {1 : 25, 2 : 25, 3 : 22, 4 : 19, 5 : 14}], '2 Peter' : [3, {1 : 21, 2 : 22, 3 : 18}], '1 John' : [5, {1 : 10, 2 : 29, 3 : 24, 4 : 21, 5 : 21}], '2 John' : [1, {1 : 13}], '3 John' : [1, {1 : 14}], 'Jude' : [1, {1 : 25}], 'Revelation' : [22, {1 : 20, 2 : 29, 3 : 22, 4 : 11, 5 : 14, 6 : 17, 7 : 17, 8 : 13, 9 : 21, 10 : 11, 11 : 19, 12 : 17, 13 : 18, 14 : 20, 15 : 8, 16 : 21, 17 : 18, 18 : 24, 19 : 21, 20 : 15, 21 : 27, 22 : 21}], '1 Esdras' : [9, {1 : 58, 2 : 30, 3 : 24, 4 : 63, 5 : 73, 6 : 34, 7 : 15, 8 : 96, 9 : 55}], '2 Esdras' : [16, {1 : 40, 2 : 48, 3 : 36, 4 : 52, 5 : 56, 6 : 59, 7 : 70, 8 : 63, 9 : 47, 10 : 59, 11 : 46, 12 : 51, 13 : 58, 14 : 48, 15 : 63, 16 : 78}], 'Tobit' : [14, {1 : 22, 2 : 14, 3 : 17, 4 : 21, 5 : 22, 6 : 17, 7 : 18, 8 : 21, 9 : 6, 10 : 12, 11 : 19, 12 : 22, 13 : 18, 14 : 15}], 'Judith' : [16, {1 : 16, 2 : 28, 3 : 10, 4 : 15, 5 : 24, 6 : 21, 7 : 32, 8 : 36, 9 : 14, 10 : 23, 11 : 23, 12 : 20, 13 : 20, 14 : 19, 15 : 13, 16 : 25}], 'Additions to Esther' : [16, {1 : 1, 10 : 10, 11 : 12, 12 : 6, 13 : 18, 14 : 19, 15 : 16, 16 : 24}], 'Wisdom of Solomon' : [19, {1 : 16, 2 : 24, 3 : 19, 4 : 20, 5 : 23, 6 : 25, 7 : 30, 8 : 21, 9 : 18, 10 : 21, 11 : 26, 12 : 27, 13 : 19, 14 : 31, 15 : 19, 16 : 29, 17 : 21, 18 : 25, 19 : 22}], 'Ecclesiasticus' : [51, {1 : 30, 2 : 18, 3 : 31, 4 : 31, 5 : 15, 6 : 37, 7 : 36, 8 : 19, 9 : 18, 10 : 31, 11 : 34, 12 : 18, 13 : 26, 14 : 27, 15 : 20, 16 : 30, 17 : 32, 18 : 33, 19 : 30, 20 : 32, 21 : 28, 22 : 27, 23 : 28, 24 : 34, 25 : 26, 26 : 29, 27 : 30, 28 : 26, 29 : 28, 30 : 25, 31 : 31, 32 : 24, 33 : 31, 34 : 26, 35 : 20, 36 : 26, 37 : 31, 38 : 34, 39 : 35, 40 : 30, 41 : 24, 42 : 25, 43 : 33, 44 : 23, 45 : 26, 46 : 20, 47 : 25, 48 : 25, 49 : 16, 50 : 29, 51 : 30}], 'Baruch' : [6, {1 : 22, 2 : 35, 3 : 37, 4 : 37, 5 : 9, 6 : 73}], 'Prayer of Azariah' : [1, {1 : 67}], 'Susanna' : [1, {1 : 64}], 'Bel and the Dragon' : [1, {1 : 42}], 'Prayer of Manasseh' : [1, {1 : 1}], '1 Maccabees' : [16, {1 : 64, 2 : 70, 3 : 60, 4 : 61, 5 : 68, 6 : 63, 7 : 50, 8 : 32, 9 : 73, 10 : 89, 11 : 74, 12 : 53, 13 : 53, 14 : 49, 15 : 41, 16 : 24}], '2 Maccabees' : [15, {1 : 36, 2 : 32, 3 : 40, 4 : 50, 5 : 27, 6 : 31, 7 : 42, 8 : 36, 9 : 29, 10 : 38, 11 : 38, 12 : 45, 13 : 26, 14 : 46, 15 : 39}]}

	the_reference = ''
	previous_versenum = 0
	next_versenum = 0
	the_previous = ''
	the_next = ''

	b_c_v_search = False

	if reference != None:
		reference = reference.lower().strip()

		if 'psalms' in reference:
			reference = reference.replace('psalms', 'psalm')

		if any(c.isalpha() for c in reference):

			if ':' not in reference:

				if not any(c.isdigit() for c in reference[1:]):

					if reference in the_books_lower:
						the_reference = the_books[the_books_lower.index(reference)] + ' 1:1'

				else:
					if ' ' in reference:
						the_book = reference.rsplit(' ', 1)[0].strip()

						if the_book in the_books_lower:
							the_book = the_books[the_books_lower.index(the_book)]

							first_n = reference.rsplit(' ', 1)[1]

							if first_n.isdigit():
								first_n = int(first_n)

								if first_n > 0:
									check_c = the_refs[the_book][0]

									if first_n <= check_c:
										the_reference = the_book + ' ' + str(first_n) + ':1'

									else:
										the_reference = the_book + ' ' + str(check_c) + ':1'

								else:
									the_reference = the_book + ' 1:1'

							else:
								the_reference = the_book + ' 1:1'

			else:
				if ' ' in reference:
					the_book = reference.rsplit(' ', 1)[0].strip()

					if the_book in the_books_lower:
						the_book = the_books[the_books_lower.index(the_book)]

						first_n = reference.split(':', 1)[0].rsplit(' ', 1)[1]

						if first_n.isdigit():
							first_n = int(first_n)

							if first_n > 0:
								check_c = the_refs[the_book][0]

								if first_n <= check_c:
									the_reference = the_book + ' ' + str(first_n)

									second_n = reference.split(':', 1)[1]

									if second_n.isdigit():
										second_n = int(second_n)

										if second_n > 0:
											check_v = the_refs[the_book][1][first_n]

											if second_n <= check_v:
												the_reference += ':' + str(second_n)

											else:
												the_reference += ':' + str(check_v)

										else:
											the_reference += ':1'

									else:
										the_reference += ':1'

								else:
									the_reference = the_book + ' ' + str(check_c) + ':1'

							else:
								the_reference = the_book + ' 1:1'

						else:
							the_reference = the_book + ' 1:1'

		if the_reference != '':

			reference = the_reference

			the_book = the_reference.rsplit(' ', 1)[0]
			c_num = int(the_reference.split(':', 1)[0].rsplit(' ', 1)[1])
			v_num = int(the_reference.split(':', 1)[1])

			max_chapter = the_refs[the_book][0]
			max_verse = the_refs[the_book][1][c_num]

			the_book_index = the_books.index(the_book)

			if the_book_index < 66:
				all_previous_books = the_books[0:the_book_index]
				previous_verse_count = 0

				for previous_book in all_previous_books:
					previous_verse_count += sum(the_refs[previous_book][1].values())

				previous_verse_count += v_num

				if c_num > 1:
					for i in range(1, c_num):
						previous_verse_count += the_refs[the_book][1][i]

				versenum = previous_verse_count

				if versenum == 1:
					previous_versenum = 31102
					next_versenum = 2
				elif versenum == 31102:
					previous_versenum = 31101
					next_versenum = 1
				else:
					previous_versenum = versenum - 1
					next_versenum = versenum + 1

			if the_reference == 'Genesis 1:1':
				the_previous = 'Revelation 22:21'
				the_next = 'Genesis 1:2'
			elif the_reference == 'Revelation 22:21':
				the_previous = 'Revelation 22:20'
				the_next = 'Genesis 1:1'
			elif the_reference == '1 Esdras 1:1':
				the_previous = ''
				the_next = '1 Esdras 1:2'
			elif the_reference == '2 Maccabees 15:39':
				the_previous = '2 Maccabees 15:38'
				the_next = ''
			else:
				if v_num < max_verse:
					the_next = the_book + ' ' + str(c_num) + ':' + str(v_num + 1)
				elif c_num + 1 <= max_chapter:
					the_next = the_book + ' ' + str(c_num + 1) + ':1'
				else:
					the_next = the_books[the_book_index + 1] + ' 1:1'

				if c_num == 1:
					if v_num > 1:
						the_previous = the_book + ' ' + str(c_num) + ':' + str(v_num - 1)
					else:
						book_previous = the_books[the_book_index - 1]
						max_chapter_previous = the_refs[book_previous][0]
						max_verse_previous = the_refs[book_previous][1][max_chapter_previous]
						the_previous = book_previous + ' ' + str(max_chapter_previous) + ':' + str(max_verse_previous)

				else:
					if v_num > 1:
						the_previous = the_book + ' ' + str(c_num) + ':' + str(v_num - 1)
					else:
						max_verse_previous = the_refs[the_book][1][c_num - 1]
						the_previous = the_book + ' ' + str(c_num - 1) + ':' + str(max_verse_previous)

			if the_book_index > 65:
				return apoc(the_reference, the_previous, the_next)

		else:
			reference = 'Genesis 1:1'
			versenum = 1
			previous_versenum = 31102
			next_versenum = 2

	elif versenum != None:
		versenum = versenum.strip()

		if not versenum.isdigit() or versenum == '0':
			versenum = 1

		versenum = int(versenum)

		if versenum > 31102:
			versenum = 31102

		if versenum == 1:
			previous_versenum = 31102
			next_versenum = 2
		elif versenum == 31102:
			previous_versenum = 31101
			next_versenum = 1
		else:
			previous_versenum = versenum - 1
			next_versenum = versenum + 1

	elif book != None and chapter != None and verse != None:
		book = book.strip()
		chapter = chapter.strip()
		verse = verse.strip()

		try:
			if book.isdigit() and chapter.isdigit() and verse.isdigit() and book != '0' and chapter != '0' and verse != '0':
				book = int(book)
				chapter = int(chapter)
				verse = int(verse)

				if book <= 66 and chapter <= the_refs[the_books[book - 1]][0] and verse <= the_refs[the_books[book - 1]][1][chapter]:
					b_c_v_search = True

					all_previous_books = the_books[0:book - 1]
					previous_verse_count = 0

					for previous_book in all_previous_books:
						previous_verse_count += sum(the_refs[previous_book][1].values())

					previous_verse_count += verse

					if chapter > 1:
						for i in range(1, chapter):
							previous_verse_count += the_refs[the_books[book - 1]][1][i]

					versenum = previous_verse_count

					if versenum == 1:
						previous_versenum = 31102
						next_versenum = 2
					elif versenum == 31102:
						previous_versenum = 31101
						next_versenum = 1
					else:
						previous_versenum = versenum - 1
						next_versenum = versenum + 1

				else:
					raise

			else:
				raise

		except:
			versenum = 1
			previous_versenum = 31102
			next_versenum = 2

	else:
		versenum = 1
		previous_versenum = 31102
		next_versenum = 2

	# ---------------------------------------------------

	cookie = request.cookies.get('bible_select')
	if cookie == None or (cookie != None and (cookie != 'kjv_select' and cookie != 'av_select')) : cookie = 'kjv_select'

	cookie2 = request.cookies.get('greek_select')
	if cookie2 == None or (cookie2 != None and (cookie2 != 'TR1894' and cookie2 != 'Stephanus1550')) : cookie2 = 'TR1894'

	return explorer_view(versenum, previous_versenum, next_versenum, cookie, cookie2)



@cache.memoize(timeout=536112000)
def strongs_html(strongsnumber):
	db = dataset.connect(DB_PATH)
	Strongs = db['Strongs_']

	rows = []

	for result in db.query('SELECT * FROM Complete WHERE SNs_ LIKE :sn', {'sn' : '%~' + strongsnumber + '~%'}): rows.append(result)
	definition = Strongs.find_one(StrongsNumber=strongsnumber)

	if definition != None:
		if definition['Root'] == None:
			definition = None

	if definition != None:
		definition = '<div class="strongs_definition" id="infobox">' + Create_Strongs_Definition(definition) + '</div>\n\n'
	else:
		definition = ''

	page = page_head.replace('{{{TITLE}}}', 'Bible Gematria Explorer | Search Results') + """<div class="m_1 left">
<table class="m_3 box2">
	<thead>
		<tr>
			<th colspan="2" class="light">Search Results - {{{result_string}}}</th>
		</tr>
		<tr>
			<th class="fill" colspan="2">All verses containing Strong's Hebrew word number <span class="regular">""" + strongsnumber + """</span></th>
		</tr>
		<tr>
			<th>Book</th>
			<th>Verses</th>
		</tr>
	</thead>
	<tbody>
{{{search_results_HTML}}}
	</tbody>
</table>
</div>

<div class="m_1 left">
""" + definition + search_group_1 + '\n\n' + search_group_2 + '\n\n' + CodesHTML + '\n</div>' + page_foot

	#----------------------------------

	search_results_HTML = """		<tr>
			<td>&nbsp;</td>
			<td>&nbsp;</td>
		</tr>"""

	result_string = ''

	if len(rows) == 0:	
		result_string = 'No results'

		return page.replace('{{{result_string}}}', result_string).replace('{{{search_results_HTML}}}', search_results_HTML).replace('{{{bnum}}}', '1').replace('{{{cnum}}}', '1').replace('{{{vnum}}}', '1')

	#----------------------------------

	num_verses_results = len(rows)
	num_books_results = len(list(set([item['book'] for item in rows])))

	result_string = str(num_verses_results) + ' verse'
	if num_verses_results > 1: result_string += 's'
	result_string += ' found in ' + str(num_books_results) + ' book'
	if num_books_results > 1: result_string += 's'

	bnum = rows[0]['bnum']
	cnum = rows[0]['cnum']
	vnum = rows[0]['vnum']

	books_list = []
	bcv_list = []

	for item in rows:
		if item['book'] not in books_list:
			books_list.append(item['book'])
			bcv_list.append([])

		bcv_list[len(books_list) - 1].append([item['bnum'], item['cnum'], item['vnum']])

	search_results_HTML = ''

	for book, bcv_l in zip(books_list, bcv_list):
		search_results_HTML += '		<tr>\n'
		search_results_HTML += '			<td class="nowrap">' + book + '</td>\n'
		search_results_HTML += '			<td>'

		for bcv in bcv_l:
			search_results_HTML += '<a href="/explorer?book=' + str(bcv[0]) + '&chapter=' + str(bcv[1]) + '&verse=' + str(bcv[2]) + '" class="blue">' + str(bcv[1]) + ':' + str(bcv[2]) + '</a>, '

		search_results_HTML = search_results_HTML[:-2]
		search_results_HTML += '</td>\n'
		search_results_HTML += '		</tr>\n'

	search_results_HTML = search_results_HTML[:-1]

	return page.replace('{{{result_string}}}', result_string).replace('{{{search_results_HTML}}}', search_results_HTML).replace('{{{bnum}}}', str(bnum)).replace('{{{cnum}}}', str(cnum)).replace('{{{vnum}}}', str(vnum))



@app.route('/strongs', methods=['GET'])
def strongs():
	strongsnumber = request.args.get('strongsnumber')

	if strongsnumber == None: strongsnumber = 'H2442'
	strongsnumber = strongsnumber.strip()
	if len(strongsnumber) < 2: strongsnumber = 'H2442'
	if (strongsnumber[:1].upper() != 'H' and strongsnumber[:1].upper() != 'G') or (not strongsnumber[1:].isdigit()): strongsnumber = 'H2442'
	if (strongsnumber[:1].upper() == 'H' and int(strongsnumber[1:]) > 8674) or (strongsnumber[:1].upper() == 'G' and int(strongsnumber[1:]) > 5624): strongsnumber = 'H2442'
	strongsnumber = strongsnumber[:1].upper() + strongsnumber[1:].lstrip('0')

	return strongs_html(strongsnumber)



@cache.memoize(timeout=536112000)
def gematria_html(value):
	db = dataset.connect(DB_PATH)
	Strongs = db['Strongs_']

	rows = []
	rows2 = []

	for result in db.query('SELECT * FROM Complete WHERE Original_Words_values LIKE :otv LIMIT ' + str(ROW_RESULT_LIMIT), {'otv' : '%~' + str(value) + '~%'}): rows.append(result)
	for result in db.query('SELECT * FROM Complete WHERE total = :value', {'value' : value}): rows2.append(result)

	word_results = []
	verse_results = []

	for row in rows:
		StrongsNumber = row['Original_Words_SN'].strip('{').strip('}').strip('~').split('~')
		Original_Words = row['Original_Words'].split('~')
		Original_Words_values = row['Original_Words_values'].strip('{').strip('}').strip('~').split('~')

		Language = 'H'

		if row['id'] > 23145:
			Language = 'G'

		for SN, OW, OWV in zip(StrongsNumber, Original_Words, Original_Words_values):
			if OWV == 'NONE':
				continue

			if int(OWV) == value:
				word_results.append({'ref' : row['ref'], 'bnum' : row['bnum'], 'cnum' : row['cnum'], 'vnum' : row['vnum'], 'SN' : SN, 'OW' : OW, 'Language' : Language})

	for row in rows2:
		verse_results.append({'ref' : row['ref'], 'bnum' : row['bnum'], 'cnum' : row['cnum'], 'vnum' : row['vnum'], 'text_1769' : row['text_1769']})

	All_StrongsNumbers = []

	H_count = 0
	G_count = 0

	for word in word_results:
		if word['SN'] not in All_StrongsNumbers: All_StrongsNumbers.append(word['SN'])
		if 'H' in word['Language']: H_count += 1
		if 'G' in word['Language']: G_count += 1

	results = Strongs.find(StrongsNumber=All_StrongsNumbers)

	AllStrongsNumbersHTML = ''
	StrongsNumber_data = {}

	for result in results:
		AllStrongsNumbersHTML += '<div id="' + result['StrongsNumber'] + '" hidden>' + Create_Strongs_Definition(result) + '</div>\n'
		StrongsNumber_data.update({result['StrongsNumber'] : {'Transliteration' : result['Transliteration'], 'Meaning' : result['Meaning'], 'Transliteration1' : result['Transliteration1']}})

	AllStrongsNumbersHTML = AllStrongsNumbersHTML[:-1]

	books = []

	for verse in verse_results:
		if verse['bnum'] not in books: books.append(verse['bnum'])

	v_count = len(verse_results)
	b_count = len(books)

	result_string1 = ''

	if H_count == 0 and G_count == 0:
		result_string1 = 'No results'

	if H_count > 0:
		result_string1 += str(H_count) + ' Hebrew word'
		if H_count > 1: result_string1 += 's'
		if G_count > 0: result_string1 += ', '

	if G_count > 0:
		result_string1 += str(G_count) + ' Greek word'
		if G_count > 1: result_string1 += 's'

	if len(rows) == ROW_RESULT_LIMIT: result_string1 += ' (' + str(ROW_RESULT_LIMIT) + ' row result limit reached)'

	result_string2 = ''

	if v_count == 0:
		result_string2 = 'No results'

	if v_count > 0:
		result_string2 = str(v_count) + ' verse'
		if v_count > 1: result_string2 += 's'
		result_string2 += ' found in ' + str(b_count) + ' book'
		if b_count > 1: result_string2 += 's'

	search_results_HTML1 = """
		<tr>
			<td>&nbsp;</td>
			<td>&nbsp;</td>
			<td>&nbsp;</td>
		</tr>"""

	search_results_HTML2 = """
		<tr>
			<td>&nbsp;</td>
			<td>&nbsp;</td>
		</tr>"""

	if result_string1 != 'No results': search_results_HTML1 = ''

	first_result = None

	for word in word_results:
		if first_result == None: first_result = [str(word['bnum']), str(word['cnum']), str(word['vnum'])]

		lang = 'hebrew'
		if word['Language'] == 'G': lang = 'greek'

		SN_Meaning = ''

		SN_Width_tag = ' s-' + str(len(word['SN']) - 1)

		if word['SN'] != 'NONE':
			if lang == 'hebrew':
				SN_Meaning = Hebrew_Translit_Rules(StrongsNumber_data[word['SN']]['Transliteration1']) + ' - ' + StrongsNumber_data[word['SN']]['Meaning']
			else:
				SN_Meaning = Greek_Translit_Rules(StrongsNumber_data[word['SN']]['Transliteration']) + ' - ' + StrongsNumber_data[word['SN']]['Meaning']
		else:
			SN_Width_tag = ''

		search_results_HTML1 += '\n		<tr>\n'
		search_results_HTML1 += '			<td><a href="/explorer?book=' + str(word['bnum']) + '&chapter=' + str(word['cnum']) + '&verse=' + str(word['vnum']) + '" class="blue">' + word['ref'] + '</a></td>\n'
		search_results_HTML1 += '			<td class="open_sans"><span class="strongs' + SN_Width_tag + '" data="' + word['SN'] + '">' + word['SN'] + '</span>' + SN_Meaning + '</td>\n'
		search_results_HTML1 += '			<td class="' + lang + '">' + word['OW'] + '</td>\n'
		search_results_HTML1 += '		</tr>'

	if result_string2 != 'No results': search_results_HTML2 = ''

	for verse in verse_results:
		if first_result == None: first_result = [str(verse['bnum']), str(verse['cnum']), str(verse['vnum'])]

		search_results_HTML2 += '\n		<tr>\n'
		search_results_HTML2 += '			<td><a href="/explorer?book=' + str(verse['bnum']) + '&chapter=' + str(verse['cnum']) + '&verse=' + str(verse['vnum']) + '" class="blue nowrap">' + verse['ref'] + '</a></td>\n'
		search_results_HTML2 += '			<td>' + verse['text_1769'] + '</td>\n'
		search_results_HTML2 += '		</tr>'

	if AllStrongsNumbersHTML != '': AllStrongsNumbersHTML += '\n\n'

	if first_result == None: first_result = ['1', '1', '1']

	page = page_head.replace('{{{TITLE}}}', 'Bible Gematria Explorer | Search Results') + AllStrongsNumbersHTML + """<div class="m_1 left">
<table class="m_3 box2">
	<thead>
		<tr>
			<th colspan="3" class="light">Search Results - """ + result_string1 + """</th>
		</tr>
		<tr>
			<th class="fill" colspan="3">All words in the Bible with a value of <span class="regular">""" + str(value) + """</span></th>
		</tr>
		<tr>
			<th>Reference</th>
			<th>Strong's #</th>
			<th>Original text</th>
		</tr>
	</thead>
	<tbody>""" + search_results_HTML1 + """
	</tbody>
</table>

<table class="m_3 box2 clear">
	<thead>
		<tr>
			<th colspan="2" class="light">Search Results - """ + result_string2 + """</th>
		</tr>
		<tr>
			<th class="fill" colspan="2">All verses in the Bible with a total of <span class="regular">""" + str(value) + """</span></th>
		</tr>
		<tr>
			<th>Reference</th>
			<th>Verse text</th>
		</tr>
	</thead>
	<tbody>""" + search_results_HTML2 + """
	</tbody>
</table>
</div>

<div class="m_1 left">
<div class="plain2" id="infobox">Info box. Click on a Strong's # to view its definition.</div>

""" + search_group_1.replace('{{{bnum}}}', first_result[0]).replace('{{{cnum}}}', first_result[1]).replace('{{{vnum}}}', first_result[2]) + '\n\n' + search_group_2 + '\n\n' + CodesHTML + '\n</div>' + page_foot

	return page



@app.route('/gematria', methods=['GET'])
def gematria():
	value = request.args.get('value')

	if value == None:
		value = '1489'
	else:
		value = value.strip()

	if not value.isdigit(): value = 1489
	if int(value) < 1 or int(value) > 40000: value = 1489
	value = int(value)

	return gematria_html(value)



@cache.memoize(timeout=536112000)
def english_html(words):
	db = dataset.connect(DB_PATH)

	rows = []

	for result in db.query("SELECT * FROM Complete WHERE REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(text_1769, '</i>', ''), '<i>', ''), '</divine>', ''), '<divine>', ''), '</inscription>', ''), '<inscription>', ''), '</psalmheader>', ''), '<psalmheader>', ''), '</headingletter>', ''), '<headingletter>', ''), '</colophon>', ''), '<colophon>', '') LIKE :words LIMIT " + str(ROW_RESULT_LIMIT), {'words' : '%' + words + '%'}): rows.append(result)

	#----------------------------------

	page = page_head.replace('{{{TITLE}}}', 'Bible Gematria Explorer | Search Results') + """<div class="m_1 left">
<table class="m_3 box3">
	<thead>
		<tr>
			<th colspan="2">Search Results - {{{result_string}}}</th>
		</tr>
		<tr>
			<th colspan="2">All verses containing the string "<span class="regular">{{{the_string}}}</span>"</th>
		</tr>
		<tr>
			<th>Reference</th>
			<th>Verse text</th>
		</tr>
	</thead>
	<tbody>
{{{search_results_HTML}}}
	</tbody>
</table>
</div>

<div class="m_1 left">
""" + search_group_1 + '\n\n' + search_group_2 + '\n\n' + CodesHTML + '\n</div>' + page_foot

	#----------------------------------

	search_results_HTML = """		<tr>
			<td>&nbsp;</td>
			<td>&nbsp;</td>
		</tr>"""

	result_string = ''

	if len(rows) == 0:	
		result_string = 'No results'

		return page.replace('{{{result_string}}}', result_string).replace('{{{search_results_HTML}}}', search_results_HTML).replace('{{{bnum}}}', '1').replace('{{{cnum}}}', '1').replace('{{{vnum}}}', '1').replace('{{{the_string}}}', escape(words))

	#----------------------------------

	num_verses_results = len(rows)
	num_books_results = len(list(set([item['book'] for item in rows])))

	result_string = str(num_verses_results) + ' verse'
	if num_verses_results > 1: result_string += 's'
	result_string += ' found in ' + str(num_books_results) + ' book'
	if num_books_results > 1: result_string += 's'

	if len(rows) == ROW_RESULT_LIMIT: result_string += ' (' + str(ROW_RESULT_LIMIT) + ' row result limit reached)'

	bnum = rows[0]['bnum']
	cnum = rows[0]['cnum']
	vnum = rows[0]['vnum']

	search_results_HTML = ''

	for row in rows:
		verse_text = row['text_1769'].replace('<i>', '{START_ITALIC}').replace('</i>', '{END_ITALIC}')
		verse_text = remove_tags(verse_text, '<', '>')
		verse_text = verse_text.replace('{START_ITALIC}', '<i>').replace('{END_ITALIC}', '</i>')
		verse_text = find_and_replace_html(words, verse_text)

		search_results_HTML += '		<tr>\n'
		search_results_HTML += '			<td><a href="/explorer?book=' + str(row['bnum']) + '&chapter=' + str(row['cnum']) + '&verse=' + str(row['vnum']) + '" class="blue nowrap">' + row['ref'] + '</a></td>\n'
		search_results_HTML += '			<td>' + verse_text + '</td>\n'
		search_results_HTML += '		</tr>\n'

	search_results_HTML = search_results_HTML[:-1]

	return page.replace('{{{result_string}}}', result_string).replace('{{{search_results_HTML}}}', search_results_HTML).replace('{{{bnum}}}', str(bnum)).replace('{{{cnum}}}', str(cnum)).replace('{{{vnum}}}', str(vnum)).replace('{{{the_string}}}', escape(words))



@app.route('/english', methods=['GET'])
def english():
	words = request.args.get('words')

	if words == None: words = 'hammer'
	if not any(c.isalpha() for c in words): words = 'hammer'		# The words don't contain a single letter
	if len(words) > 66 or len(words) == 1: words = 'hammer'

	return english_html(words)