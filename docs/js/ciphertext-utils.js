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

global.CiphertextUtils = {
    expandAlphabet: expandAlphabet,
    cleanCiphertext: cleanCiphertext,
};

})(window);
