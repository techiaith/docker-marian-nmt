'use strict';

(function($) {

  function setSelectionRange(input, selectionStart, selectionEnd) {
    if (input.setSelectionRange) {
      input.setSelectionRange(selectionStart, selectionEnd);
    } else if (input.createTextRange) {
      var range = input.createTextRange();
      range.collapse(true);
      range.moveEnd('character', selectionEnd);
      range.moveStart('character', selectionStart);
      range.select();
    }
  }

  const setCaretToPos = (input, pos) => setSelectionRange(input, pos, pos);

  async function handleTranslation(text) {
    const data = {
      "text": text
    };
    const response = await fetch('/api/translate', {
      body: JSON.stringify(data),
      headers: {
        'Content-Type': 'application/json',
      },
      method: 'POST'
    });
    const obj = await response.json();
    const translated = obj.translated || [];
    const result = {text: translated};
    return result;
  };

  function translate(sourceText) {
    handleTranslation(sourceText)
      .then(function(translated) {
        $('#translation')
          .removeAttr('disabled')
          .val(translated.text)
          .data('bitext',
                {source: sourceText,
                 target: translated.text})
          .attr('readonly', true)
          .trigger('change');
      })
      .catch((err) => showError(err.toString()))
  }

  function alreadyTranslated() {
    const sourceText = $('#source_text').val();
    const translation = $('#translation').val();
    const bitext = $('#translation').data('bitext');
    return (bitext && bitext.target == translation && bitext.source == sourceText);
  }

  function showError(error) {
    $('#translation-errors').empty().text(error);
  }

  function copyToClipboard(text) {
    var $temp = $('<input>')
        .val(text)
        .appendTo($('body'))
        .select();
    document.execCommand('copy');
    $temp.remove();
  }

  function configureFrontMatter() {
    $('#blywddyn').html(new Date().getFullYear());
  }

  function configureCopyTranslation() {
    $('.fa-copy')
      .mouseenter(function() {
        $(this)
          .removeClass('fa-regular')
          .addClass('fa-solid');
      }).mouseleave(function() {
        $(this)
          .removeClass('fa-solid')
          .addClass('fa-regular');
      }).click(function(e) {
        copyToClipboard($('#translation').val());
      });
  }

  function enableButton(selector) {
    return $(selector).removeClass('disabled').removeAttr('disabled');
  }

  function disableButton(selector) {
    return $(selector).addClass('disabled').attr('disabled', true);
  }

  function configureTranslationBehaviour() {
    const translator = $('#translator').on('submit', (e) => {
      e.preventDefault();
      const sourceTextElem = $('#source_text');
      const sourceText = sourceTextElem.val().trim();
      if (sourceText.length > 0 && !alreadyTranslated()) {
        translate(sourceText);
        enableButton('#btn-reset');
      }
      disableButton('#btn-translate');
    });
    $('#btn-reset')
      .closest('form')
      .on('reset', (e) => {
        $('#translation-disabled-message').trigger('close.bs.alert');
        $('#source_text').empty();
        $('#translation')
          .data('bitext', {source: null, target: null})
          .val('');
      });
    $('#source_text')
      .on('change input propertychange', (e) => {
        $('#translation-disabled-message').trigger('close.bs.alert');
        if (alreadyTranslated()) {
          $('#warning-message')
            .text("Wedi'i cyfieithu yn barod")
            .parent()
            .toggleClass('hide show');
          disableButton('#btn-translate');
        } else {
          enableButton('#btn-translate');
        }
        enableButton('#btn-reset');
      })
      .on('focus', (e) => {
        const elem = $(e.target);
        const text = elem.val();
        setCaretToPos(elem[0], text.length ? text.length: 0);
      });
    $('#translation')
      .on('change', (e) => {
        enableButton('#btn-reset');
        disableButton('#btn-translate');
      });
    $('#source_text').empty();
  }

  $(document).ready(function(e) {
    configureFrontMatter();
    configureCopyTranslation();
    configureTranslationBehaviour();
  });

})(jQuery);
