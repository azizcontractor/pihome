function test(hello) {
  alert(hello);
}

function show_ajax_error(error_dict) {
  var modals = document.getElementsByName("modal");
  for (var i = 0; i < modals.length; i++) {
    if (modals[i].style.display == "block") {
      modals[i].style.display = "none";
    }
  }
  error_str = error_dict["status"] + " - " + error_dict["statusText"];
  $("div#alert_div").html(
    "An error occured while performing your request.<br/><b>ERROR MESSAGE:</b> " + error_str
  );
  $("div#error_modal").show();
}

function getCookie(name) {
  let cookieValue = null;
  if (document.cookie && document.cookie !== "") {
    const cookies = document.cookie.split(";");
    for (let i = 0; i < cookies.length; i++) {
      const cookie = cookies[i].trim();
      // Does this cookie string begin with the name we want?
      if (cookie.substring(0, name.length + 1) === name + "=") {
        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
        break;
      }
    }
  }
  return cookieValue;
}

(function ($) {
  $.each(["show", "hide"], function (i, ev) {
    var el = $.fn[ev];
    $.fn[ev] = function () {
      this.trigger(ev);
      return el.apply(this, arguments);
    };
  });
})(jQuery);

function strftime(sFormat, date) {
  if (!(date instanceof Date)) date = new Date();
  var nDay = date.getDay(),
    nDate = date.getDate(),
    nMonth = date.getMonth(),
    nYear = date.getFullYear(),
    nHour = date.getHours(),
    aDays = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"],
    aMonths = [
      "January",
      "February",
      "March",
      "April",
      "May",
      "June",
      "July",
      "August",
      "September",
      "October",
      "November",
      "December",
    ],
    aDayCount = [0, 31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334],
    isLeapYear = function () {
      return (nYear % 4 === 0 && nYear % 100 !== 0) || nYear % 400 === 0;
    },
    getThursday = function () {
      var target = new Date(date);
      target.setDate(nDate - ((nDay + 6) % 7) + 3);
      return target;
    },
    zeroPad = function (nNum, nPad) {
      return ("" + (Math.pow(10, nPad) + nNum)).slice(1);
    };
  return sFormat.replace(/%-?[a-z]/gi, function (sMatch) {
    return (
      {
        "%a": aDays[nDay].slice(0, 3),
        "%A": aDays[nDay],
        "%b": aMonths[nMonth].slice(0, 3),
        "%B": aMonths[nMonth],
        "%c": date.toUTCString(),
        "%C": Math.floor(nYear / 100),
        "%d": zeroPad(nDate, 2),
        "%e": nDate,
        "%F": date.toISOString().slice(0, 10),
        "%G": getThursday().getFullYear(),
        "%g": ("" + getThursday().getFullYear()).slice(2),
        "%H": zeroPad(nHour, 2),
        "%I": zeroPad(((nHour + 11) % 12) + 1, 2),
        "%-I": ((nHour + 11) % 12) + 1,
        "%j": zeroPad(aDayCount[nMonth] + nDate + (nMonth > 1 && isLeapYear() ? 1 : 0), 3),
        "%k": "" + nHour,
        "%l": ((nHour + 11) % 12) + 1,
        "%m": zeroPad(nMonth + 1, 2),
        "%M": zeroPad(date.getMinutes(), 2),
        "%p": nHour < 12 ? "AM" : "PM",
        "%P": nHour < 12 ? "am" : "pm",
        "%s": Math.round(date.getTime() / 1000),
        "%S": zeroPad(date.getSeconds(), 2),
        "%u": nDay || 7,
        "%V": (function () {
          var target = getThursday(),
            n1stThu = target.valueOf();
          target.setMonth(0, 1);
          var nJan1 = target.getDay();
          if (nJan1 !== 4) target.setMonth(0, 1 + ((4 - nJan1 + 7) % 7));
          return zeroPad(1 + Math.ceil((n1stThu - target) / 604800000), 2);
        })(),
        "%w": "" + nDay,
        "%x": date.toLocaleDateString(),
        "%X": date.toLocaleTimeString(),
        "%y": ("" + nYear).slice(2),
        "%Y": nYear,
        "%z": date.toTimeString().replace(/.+GMT([+-]\d+).+/, "$1"),
        "%Z": date.toTimeString().replace(/.+\((.+?)\)$/, "$1"),
      }[sMatch] || sMatch
    );
  });
}
