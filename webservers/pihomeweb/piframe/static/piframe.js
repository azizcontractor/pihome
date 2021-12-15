function display_img(img_src) {
  var img_div = document.getElementById("img_div");
  var img = document.getElementById("current_img");
  if (img_src == null) {
    var xdiv = document.getElementById('nopicsdiv');
    if (xdiv == null) {
      xdiv = document.createElement('div');
      xdiv.id = 'nopicsdiv';
      img_div.appendChild(xdiv);
    }
    xdiv.innerHTML = "";
    var h3 = document.createElement("h3");
    h3.className = "w3-center";
    h3.innerText = "No Images uploaded to the server.";
    var icon = document.createElement("i");
    icon.className = "fas fa-exclamation-circle w3-text-red fa-9x";
    xdiv.appendChild(icon);
    xdiv.appendChild(h3);
  } else {
    var img = document.getElementById("current_img");
    if (img == null) {
      var xdiv = document.getElementById('nopicsdiv');
      if (xdiv != null) {
        img_div.removeChild(xdiv);
      }
      var img = document.createElement("img");
      img.id = "current_img";
      img.style.maxWidth = "1400px";
      img.style.maxHeight = "1000px";
      img.style.width = "auto";
      img.style.verticalAlign = "middle";
      img.style.height = "auto";
      img.style.margin = "auto";
      img_div.appendChild(img);
    }
    var $img = $("img#current_img");
    var duration = 2000;
    $img.fadeOut(duration, function () {
      $img.on('load', function () {
        $img.fadeIn(duration);
      });
      $img.attr("src", img_src);
    });
  }
}

function load_new_img() {
  var img_div = document.getElementById("img_div");
  var nav_div = document.getElementById('nav_div');
  let max_width = $(window).width() - $("div#info_div").width();
  let max_height = $(window).height() - $("div#nav_div").height();
  $.ajax({
    url: "load_image/",
    method: "GET",
    data: {
      height: max_height,
      width: max_width,
    },
    global: false,
    success: function (response) {
      display_img(response["image"]);
    },
  });
}
