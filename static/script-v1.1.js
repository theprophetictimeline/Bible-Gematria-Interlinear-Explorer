function escapeRegExp(str) {
	return str.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}

function replaceAll(str, find, replace) {
	return str.replace(new RegExp(escapeRegExp(find), 'g'), replace);
}

function split(str, find) {
	var index = str.indexOf(find);
	return [str.slice(0, index), str.slice(index + 1)];
}

function remove_tags(str, front, end) {

	while (str.indexOf(front) >= 0) {
		var tag = front + split(split(str, front)[1], end)[0] + end;
		str = replaceAll(str, tag, '');
	}

	return str;
}

function convert_English(str) {
	str = remove_tags(str, '{', '}').split('|');
	var new_text = '';

	for (var i = 0; i < str.length; i++) {
		if (str[i].indexOf('†') >= 0) {
			new_text += '<span class="medium">' + replaceAll(str[i], '†', '') + '</span> ';
		}
		else {
			new_text += str[i] + ' ';
		}
	}

	return new_text.trim();
}

function convert_Transliteration(str) {
	str = replaceAll(str, 'ə', '<span class="ee">ə</span>');

	while (str.indexOf('\u0323') >= 0) {
		str = str.replace('\u0323', '');
	}

	return str;
}

$(document).ready(function() {

	function setCookie(key, value, expiry) {
		var expires = new Date();
		expires.setTime(expires.getTime() + (expiry * 24 * 60 * 60 * 1000));
		document.cookie = key + '=' + value + '; expires=' + expires.toUTCString() + '; SameSite=None; Secure';
	}

	function getCookie(key) {
		var keyValue = document.cookie.match('(^|;) ?' + key + '=([^;]*)(;|$)');
		return keyValue ? keyValue[2] : null;
	}

	if (!getCookie('bible_select')) { setCookie('bible_select', 'kjv_select', '189'); }

	function copyToClipboard(elem) {	
		var targetId = '_hiddenCopyText_';
		var isInput = elem.tagName === 'INPUT' || elem.tagName === 'TEXTAREA';
		var origSelectionStart, origSelectionEnd;

		if (isInput) {
			target = elem;
			origSelectionStart = elem.selectionStart;
			origSelectionEnd = elem.selectionEnd;
		}

		else {
			target = document.getElementById(targetId);

			if (!target) {
				var target = document.createElement('textarea');
				target.style.position = 'absolute';
				target.style.left = '-9999px';
				target.style.top = '0';
				target.id = targetId;
				document.body.appendChild(target);
			}

			var versedata = $('.reference').text();
			if (getCookie('bible_select') == 'kjv_select') { versedata += ' (KJV) — ' + $('#KJV_verse').text(); }
			else if (getCookie('bible_select') == 'av_select') { versedata += ' (1611 Authorized Version) — ' + $('#av_verse').text(); }
			else { versedata += ' (KJV) — ' + $('#KJV_verse').text(); }
			versedata += '\n' + $('#verse_info').text() + ' — Total = ' + $('#total').attr('value');

			target.textContent = versedata;
		}

		var currentFocus = document.activeElement;
		target.focus();
		target.setSelectionRange(0, target.value.length);

		var succeed;

		try {
			succeed = document.execCommand('copy');
		}
		catch(e) {
			succeed = false;
		}

		if (currentFocus && typeof currentFocus.focus === 'function') {
			currentFocus.focus();
		}

		if (isInput) {
			elem.setSelectionRange(origSelectionStart, origSelectionEnd);
		}
		else {
			target.textContent = '';
		}

		return succeed;
	}

	try {
	document.getElementById('clipboard').addEventListener('click', function() {
		$('.copied').fadeIn(100).fadeOut(450);
		copyToClipboard(document.getElementById('KJV_verse'));
	});
	} catch(e) {}

	$(document).on('click', 'f', function() {
		var data = decodeURIComponent($(this).attr('data'));

		$('#infobox').html(data).removeClass('strongs_definition').addClass('plain2');
	});

	$('.strongs, .asn, .addsn').mouseover(function() {
		$("span[data='" + $(this).attr('data') + "']").addClass('regular');
	});

	$('.strongs, .asn, .gsn, .gsn2, .addsn').mouseleave(function() {
		$('.strongs, .asn, .gsn, .gsn2, .addsn').removeClass('regular');
	});

	$('.gsn').mouseover(function() {
		$(this).addClass('regular');
		$(this).siblings('.strongs').addClass('regular');

		for (var part of split($(this).attr('parts'), '|')[1].split('|')) {
			var tagnum = $(this).closest('tr').nextAll().find("span[data='" + part + "']").first().closest('tr').find('esv').attr('tagnum');

			$("esv[tagnum='" + tagnum + "']").each(function() {
				$(this).closest('tr').find('.strongs').first().addClass('regular');
			});
		}
	});

	$('.gsn2').mouseover(function() {
		$(this).addClass('regular');
		$(this).siblings('.strongs').addClass('regular');
		$(this).closest('tr').nextAll().slice(0, parseInt($(this).attr('parts'))).find('.strongs').addClass('regular');
	});

	$('esv').mouseover(function() {
		$('.square').remove();

		if ($("esv[tagnum='" + $(this).attr('tagnum') + "']").length > 1) {
			$("esv[tagnum='" + $(this).attr('tagnum') + "']").removeClass('no-glow').addClass('glow');
		}

		var English = '';
		var Transliteration = convert_Transliteration($(this).attr('e_tl'));
		var Gloss = '';
		var Parse = split($(this).attr('Parse'), '^')[1];

		var H2 = false;

		if ($(this).attr('English') != '') {
			English = convert_English($(this).attr('English'));
		} else if ($(this).attr('English') == '' && $(this).attr('H2') != '') {
			English = convert_English(split($(this).attr('H2'), '|')[1]);
			H2 = true;
		} else {
			English = '<span class="none-dash-2"></span>';
		}

		if ($(this).attr('Gloss') != '') {
			Gloss = convert_English($(this).attr('Gloss'));
		} else {
			Gloss = '<span class="none-dash-2"></span>';
		}

		var box = '<div class="square top"><div class="extra-top"></div><span class="esv-title">ESV:</span><span class="esv-text"><span class="esv-space"></span>' + English + '</span><div class="section-block"><div class="section-title">Transliteration:</div><div class="section-text">' + Transliteration + '</div></div><span class="gloss-title">Gloss:</span><span class="gloss-text">' + Gloss + '</span><div class="section-block"><div class="section-title">Parse:</div><div class="section-text">' + Parse + '</div></div><div class="extra-bottom"></div></div>';

		if (H2) {
			box = '<div class="square top"><div class="extra-top"></div><div class="section-block"><div class="section-text-fragment">(fragment of phrase)</div></div><span class="esv-title-fragment">ESV:</span><span class="esv-text-fragment"><span class="esv-space"></span>' + English + '</span><div class="section-block"><div class="section-title">Transliteration:</div><div class="section-text">' + Transliteration + '</div></div><span class="gloss-title">Gloss:</span><span class="gloss-text">' + Gloss + '</span><div class="section-block"><div class="section-title">Parse:</div><div class="section-text">' + Parse + '</div></div><div class="extra-bottom"></div></div>';
		}

		$(this).parent('span').append(box);

		$('.square').css('left', '+=' + (($(this).width() / 2) - 4).toString() + 'px');
	});

	$('pe').mouseover(function() {
		$('.square').remove();

		var box = '<div class="square top"><div class="extra-top"></div><div class="section-block"><div class="other-title">Pe</div><div class="other-section-text">Symbol meaning <a href="https://en.wikipedia.org/wiki/Parashah#Spacing_techniques" target="_blank" class="infolink">petuhah</a> (Open portion). Not an original letter in the manuscript.</div></div><div class="extra-bottom"></div></div>';

		$(this).parent('span').append(box);
	});

	$('samekh').mouseover(function() {
		$('.square').remove();

		var box = '<div class="square top"><div class="extra-top"></div><div class="section-block"><div class="other-title">Samekh</div><div class="other-section-text">Symbol meaning <a href="https://en.wikipedia.org/wiki/Parashah#Spacing_techniques" target="_blank" class="infolink">setumah</a> (Closed portion). Not an original letter in the manuscript.</div></div><div class="extra-bottom"></div></div>';

		$(this).parent('span').append(box);
	});

	$('reversednun').mouseover(function() {
		$('.square').remove();

		var box = '<div class="square top"><div class="extra-top"></div><div class="section-block"><div class="other-title">Reversed nun</div><div class="other-section-text">Punctuation, a <a href="https://en.wikipedia.org/wiki/Inverted_nun" target="_blank" class="infolink">letter</a></div></div><div class="extra-bottom"></div></div>';

		$(this).parent('span').append(box);
		$('.square').css('left', '-=2px');
	});

	$('gw').mouseover(function() {
		$('.square').remove();

		var Gloss = '';
		var Parse = split($(this).attr('Parse'), '^')[1];

		if ($(this).attr('Gloss') != '') {
			Gloss = $(this).attr('Gloss');
		} else {
			Gloss = '<span class="none-dash-2"></span>';
		}

		if ($(this).attr('AddStrongs')) {
			var AddStrongs = '';

			for (var part of $(this).attr('AddStrongs').split('|')) {
				if (part.split('`')[2] != 'NONE') {
					AddStrongs += ' <span class="addsn-text">(' + part.split('`')[2] + ')</span>';
				}
			}

			if (AddStrongs != '') {
				Gloss += ' ' + AddStrongs.trim();
			}
		}

		var box = '<div class="square top"><div class="extra-top"></div><span class="gloss-title-2">Gloss:</span><span class="gloss-text-2"><span class="gloss-space-2"></span>' + Gloss + '</span><div class="section-block"><div class="section-title">Parse:</div><div class="section-text">' + Parse + '</div></div><div class="extra-bottom"></div></div>';

		$(this).parent('span').append(box);

		$('.square').css('left', '+=' + (($(this).width() / 2) - 4).toString() + 'px');
	});

	$('.item_container').mouseleave(function() {
		if ($('esv').hasClass('glow')) {
			$("esv[tagnum='" + $(this).find('esv').attr('tagnum') + "']").removeClass('glow').addClass('no-glow');
		}

		$('.square').remove();
	});

	var timer;
	var waited = false;

	$('#Table1_Translit').mouseover(function() {

		timer = setTimeout(function() {

			$('.Table1 .translit').each(function() {
				$(this).attr('first', encodeURIComponent($(this).html()));
				$(this).html($(this).attr('info'));
			});

			waited = true;
		}, 1700);

	}).mouseleave(function() {

		if (waited) {
			$('.Table1 .translit').each(function() {
				$(this).html(decodeURIComponent($(this).attr('first')));
			});
		}

		clearTimeout(timer);
		waited = false;
	});

	$('#Table2_Translit').mouseover(function() {

		timer = setTimeout(function() {

			$('.Table2 .translit').each(function() {
				$(this).attr('first', encodeURIComponent($(this).html()));
				$(this).html($(this).attr('info'));
			});

			waited = true;
		}, 1700);

	}).mouseleave(function() {

		if (waited) {
			$('.Table2 .translit').each(function() {
				$(this).html(decodeURIComponent($(this).attr('first')));
			});
		}

		clearTimeout(timer);
		waited = false;
	});

	$('.strongs, .asn, .gsn, .gsn2, .addsn').click(function() {	// Strong's number is clicked
		var data = $(this).attr('data');
		var item = $('#' + data).html();

		$('#infobox').html(item).removeClass('plain2').addClass('strongs_definition');
	});

	$('#av_select').click(function() {	// Authorized Version is clicked
		var data = $('#av_verse').html();

		$('#versedisplay').html(data);
		$('#av_select').css('font-weight', '400');
		$('#kjv_select').css('font-weight', '300');

		setCookie('bible_select', 'av_select', '189');
	});

	$('#kjv_select').click(function() {	// KJV 1769 is clicked
		var data = $('#KJV_verse').html();

		$('#versedisplay').html(data);
		$('#kjv_select').css('font-weight', '400');
		$('#av_select').css('font-weight', '300');

		setCookie('bible_select', 'kjv_select', '189');
	});

	$('#TR1894').click(function() {
		var data = $('#TR1894_verse').html();

		$('#versedisplay2').html(data);
		$('.dot').css('opacity', '0');

		setCookie('greek_select', 'TR1894', '189');
	});

	$('#Stephanus1550').click(function() {
		var data = $('#Stephanus_verse').html();

		$('#versedisplay2').html(data);
		$('.dot').css('opacity', '1');

		setCookie('greek_select', 'Stephanus1550', '189');
	});

	$('.qere_tag').click(function() {
		$('.qere').toggleClass('active');
		$('.double-arrows').toggleClass('rotate');
		$('.qere_tag').toggleClass('qere-move');
	});

	$('.checkcontainer').click(function() {
		var this_obj = $(this).find('.wordval');

		if (this_obj.length) {

			this_obj.prop('checked', !this_obj.prop('checked'));

			if (this_obj.prop('checked')) {
				var total = parseInt($('#totaldisplay').html());
				var thistotal = parseInt(this_obj.attr('value'));
				total += thistotal;
				$('#totaldisplay').html(total);
			}

			if (!this_obj.prop('checked')) {
				var total = parseInt($('#totaldisplay').html());
				var thistotal = parseInt(this_obj.attr('value'));
				total -= thistotal;
				$('#totaldisplay').html(total);
			}
		}

		else {
			var this_obj = $(this).find('#total');

			this_obj.prop('checked', !this_obj.prop('checked'));

			if (this_obj.prop('checked')) {
				$('#totaldisplay').html(this_obj.attr('value'));
				$('input:checkbox').prop('checked', this_obj.prop('checked'));
			}

			if (!this_obj.prop('checked')) {
				$('#totaldisplay').html('0');
				$('input:checkbox').prop('checked', this_obj.prop('checked'));
			}
		}
	});

	$('#total').click(function() {
		if ($(this).prop('checked')) {
			$('#totaldisplay').html($(this).attr('value'));
			$('input:checkbox').prop('checked', $(this).prop('checked'));
		}

		if (!$(this).prop('checked')) {
			$('#totaldisplay').html('0');
			$('input:checkbox').prop('checked', $(this).prop('checked'));
		}
	});

	$('.wordval').click(function() {
		if ($(this).prop('checked')) {
			var total = parseInt($('#totaldisplay').html());
			var thistotal = parseInt($(this).attr('value'));
			total += thistotal;
			$('#totaldisplay').html(total);
		}

		if (!$(this).prop('checked')) {
			var total = parseInt($('#totaldisplay').html());
			var thistotal = parseInt($(this).attr('value'));
			total -= thistotal;
			$('#totaldisplay').html(total);
		}
	});

});

function addListenerMultiple(elem, str, func) {
	str.split(' ').forEach(function(e) {
		elem.addEventListener(e, func, false);
	});
}

function autocomplete(inp, list_items) {
	var currentFocus;

	addListenerMultiple(inp, 'click input', function() {
		var a, b, i, val = this.value;

		closeAllLists();

		currentFocus = -1;
		a = document.createElement('div');
		a.setAttribute('id', this.id + 'autocomplete-list');
		a.setAttribute('class', 'autocomplete-items');

		this.parentNode.appendChild(a);

		for (i = 0; i < list_items.length; i++) {
			var pos = list_items[i].toUpperCase().indexOf(val.toUpperCase());

			if (pos > -1) {
				b = document.createElement('div');
				b.innerHTML = list_items[i].substr(0, pos);
				b.innerHTML += '<span class="medium">' + list_items[i].substr(pos, val.length) + '</span>';
				b.innerHTML += list_items[i].substr(pos + val.length);
				b.innerHTML += '<input type="hidden" value="' + list_items[i] + '">';

				b.addEventListener('mouseup', function(e) {
					inp.value = this.getElementsByTagName('input')[0].value;
					closeAllLists();
				});

				b.addEventListener('mousedown', function(e) {
					e.preventDefault();
					return false;
				});

				a.appendChild(b);
			}
		}
	});

	inp.addEventListener('keydown', function(e) {
		var x = document.getElementById(this.id + 'autocomplete-list');

		if (x) {
			x = x.getElementsByTagName('div');
		} if (e.keyCode == 40) {
			currentFocus++;
			addActive(x);
		} else if (e.keyCode == 38) {
			currentFocus--;
			addActive(x);
		} else if (e.keyCode == 13 || e.keyCode == 9) {
			if (x && currentFocus > -1) {
				e.preventDefault();
				inp.value = x[currentFocus].textContent;
				closeAllLists();
			}
		}
	});

	function addActive(x) {
		if (!x) {
			return false;
		}
		removeActive(x);

		if (currentFocus >= x.length) {
			currentFocus = 0;
		} if (currentFocus < 0) {
			currentFocus = (x.length - 1);
		}

		x[currentFocus].classList.add('autocomplete-active');
	}

	function removeActive(x) {
		for (var i = 0; i < x.length; i++) {
			x[i].classList.remove('autocomplete-active');
		}
	}

	function closeAllLists(elem) {
		var x = document.getElementsByClassName('autocomplete-items');
		for (var i = 0; i < x.length; i++) {
			if (elem != x[i] && elem != inp) {
				x[i].parentNode.removeChild(x[i]);
			}
		}
	}

	document.addEventListener('click', function(e) {
		closeAllLists(e.target);
	});
}

var books = ['Genesis', 'Exodus', 'Leviticus', 'Numbers', 'Deuteronomy', 'Joshua', 'Judges', 'Ruth', '1 Samuel', '2 Samuel', '1 Kings', '2 Kings', '1 Chronicles', '2 Chronicles', 'Ezra', 'Nehemiah', 'Esther', 'Job', 'Psalm', 'Proverbs', 'Ecclesiastes', 'Song of Solomon', 'Isaiah', 'Jeremiah', 'Lamentations', 'Ezekiel', 'Daniel', 'Hosea', 'Joel', 'Amos', 'Obadiah', 'Jonah', 'Micah', 'Nahum', 'Habakkuk', 'Zephaniah', 'Haggai', 'Zechariah', 'Malachi', 'Matthew', 'Mark', 'Luke', 'John', 'Acts', 'Romans', '1 Corinthians', '2 Corinthians', 'Galatians', 'Ephesians', 'Philippians', 'Colossians', '1 Thessalonians', '2 Thessalonians', '1 Timothy', '2 Timothy', 'Titus', 'Philemon', 'Hebrews', 'James', '1 Peter', '2 Peter', '1 John', '2 John', '3 John', 'Jude', 'Revelation'];
var books2 = ['1 Esdras', '2 Esdras', 'Tobit', 'Judith', 'Additions to Esther', 'Wisdom of Solomon', 'Ecclesiasticus', 'Baruch', 'Prayer of Azariah', 'Susanna', 'Bel and the Dragon', 'Prayer of Manasseh', '1 Maccabees', '2 Maccabees'];

if (document.getElementById('input_verse_ref')) {
	autocomplete(document.getElementById('input_verse_ref'), books);
} else if (document.getElementById('input_verse_ref_apoc')) {
	autocomplete(document.getElementById('input_verse_ref_apoc'), books2);
}
