// Shared ciphertext-cleaning helpers, ported from ciphertext.py / stethoscope.html's
// createFromText. Originally duplicated inline in isomorph.html and
// find-repetitions.html; factored out here once a third tool needed it.
//
// Loaded as a plain (non-module) script via <script src="js/ciphertext-utils.js">
// so that tool pages work when opened directly from disk (file://), not just
// when served over HTTP. Everything shared is attached to the single global
// `CiphertextUtils` namespace at the bottom of this file.

(function (global) {

function expandAlphabet(charsetRe, caseSensitive) {
    var seen = {};
    var result = [];
    for (var code = 32; code <= 126; code++) {
        var ch = String.fromCharCode(code);
        var folded = caseSensitive ? ch : ch.toUpperCase();
        if (charsetRe.test(folded) && !seen[folded]) {
            seen[folded] = true;
            result.push(folded);
        }
    }
    return result.join('');
}

function cleanCiphertext(raw, charsetPattern, caseSensitive) {
    var flags = caseSensitive ? '' : 'i';
    var charsetRe = new RegExp('^(?:' + charsetPattern + ')$', flags);
    var ignoreRe  = new RegExp('^(?:\\s)$');
    var ditschar  = '-';

    var letters = [];
    var errors = [];

    for (var i = 0; i < raw.length; i++) {
        var ch = raw[i];
        var folded = caseSensitive ? ch : ch.toUpperCase();
        if (charsetRe.test(folded)) {
            letters.push(folded);
        } else if (folded === ditschar) {
            // dits (null placeholders) are silently dropped
        } else if (ignoreRe.test(ch)) {
            // whitespace silently dropped
        } else {
            if (errors.length < 20)
                errors.push("Invalid character '" + ch + "' at position " + i);
        }
    }

    if (errors.length > 0)
        throw new Error('Ciphertext contains invalid characters:\n' + errors.join('\n'));

    return letters.join('');
}

// ---- dit-aware reading (see "Dit characters" in docs/cryptml-spec.md) ----
//
// A dit marks a position where a symbol definitely exists but is unknown. Unlike
// cleanCiphertext, which discards dits and so shifts every later position, parseCiphertext
// keeps each dit as a position: it is returned as null among the symbols. A caller that wants a
// string maps null to whatever marker it uses internally (symbolsToString).
//
// `ditschar` is one character, or none: '', null and undefined all mean none, and none is the
// default, so no character is a dit unless the ciphertext says so.
//
// The dit is tested BEFORE charset. A declared dit wins over a permissive charset such as
// [\s\S], where it would otherwise be swallowed as an ordinary character.
//
// Returns { symbols: Array<string|null>, ditCount: number }. Letters are case-folded unless
// caseSensitive. Whitespace is dropped and takes no position. Anything else throws, as
// cleanCiphertext does.
function parseCiphertext(raw, charsetPattern, caseSensitive, ditschar) {
    var dit = (typeof ditschar === 'string' && ditschar.length === 1) ? ditschar : '';
    var charsetRe = new RegExp('^(?:' + charsetPattern + ')$', caseSensitive ? '' : 'i');
    var ignoreRe  = new RegExp('^(?:\\s)$');

    var symbols = [];
    var ditCount = 0;
    var errors = [];

    for (var i = 0; i < raw.length; i++) {
        var ch = raw[i];
        var folded = caseSensitive ? ch : ch.toUpperCase();
        if (dit !== '' && ch === dit) {
            symbols.push(null);
            ditCount++;
        } else if (charsetRe.test(folded)) {
            symbols.push(folded);
        } else if (ignoreRe.test(ch)) {
            // whitespace silently dropped
        } else {
            if (errors.length < 20)
                errors.push("Invalid character '" + ch + "' at position " + i);
        }
    }

    if (errors.length > 0)
        throw new Error('Ciphertext contains invalid characters:\n' + errors.join('\n'));

    return { symbols: symbols, ditCount: ditCount };
}

function symbolsToString(symbols, ditMarker) {
    return symbols.map(function (symbol) { return symbol === null ? ditMarker : symbol; }).join('');
}

// Reads one comment line of a CryptML text export ("# Date: \"..\" Time: \"..\" Ditschar: \".\"").
// Returns { date, time, ditschar } (each a string, or null when the field is absent), or null if
// the comment carries none of the three and so is an ordinary label. A block with no Ditschar
// field has no dit character.
var DATE_FIELD_RE = /Date:\s*"([^"]*)"/;
var TIME_FIELD_RE = /Time:\s*"([^"]*)"/;
var DITSCHAR_FIELD_RE = /Ditschar:\s*"(.)"/;

function parseExportMetadata(comment) {
    var date = comment.match(DATE_FIELD_RE);
    var time = comment.match(TIME_FIELD_RE);
    var dit = comment.match(DITSCHAR_FIELD_RE);
    if (!date && !time && !dit) return null;
    return {
        date: date ? date[1] : null,
        time: time ? time[1] : null,
        ditschar: dit ? dit[1] : null,
    };
}

global.CiphertextUtils = {
    expandAlphabet: expandAlphabet,
    cleanCiphertext: cleanCiphertext,
    parseCiphertext: parseCiphertext,
    symbolsToString: symbolsToString,
    parseExportMetadata: parseExportMetadata,
};

})(window);
