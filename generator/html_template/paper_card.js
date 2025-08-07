    function adjustFontSize() {
      const textElement = document.getElementById('title');
      const textLength = textElement.textContent.length;


      let fontSize = 4.4;
      if (textLength > 150) {
        fontSize = 3.4;
      } else if (textLength > 60) {
        fontSize = 3.8;
      }

      textElement.style.fontSize = fontSize + 'rem';
    }

    window.onload = adjustFontSize;