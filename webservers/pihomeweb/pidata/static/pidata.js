function get_time() {
  var time_heading = document.getElementById("time_heading");
  //   time_heading.innerText = strftime("%-I:%M %p");
  $.ajax({
    url: "/pidata/time/",
    method: "GET",
    data: {},
    global: false,
    success: function (response) {
      time_heading.innerText = response["time"];
    },
  });
}

function get_location() {
  var location_heading = document.getElementById("location_heading");
  var weather_div = document.getElementById("weather_div");
  var forecast_div = document.getElementById("forecast_div");
  $.ajax({
    url: "/pidata/location/",
    method: "GET",
    data: {},
    global: false,
    success: function (response) {
      location_heading.innerText = response["city"] + ", " + response["region"];
      get_weather(response["latitude"], response["longitude"]);
    },
    error: function (xhr, status, error) {
      location_heading.innerText = "???????";
      var icon = document.createElement("i");
      icon.className = "fas fa-exclamation-circle w3-text-red fa-9x";
      weather_div.innerHTML = "";
      weather_div.appendChild(icon);
      forecast_div.innerHTML = "";
    },
  });
}

function get_quote() {
  var quote_div = document.getElementById("quote_div");
  $.ajax({
    url: "/pidata/quote/",
    method: "GET",
    data: {},
    global: false,
    success: function (response) {
      console.log(response);
      quote_div.innerHTML = "";
      var title_h = document.createElement("h3");
      title_h.className = "w3-center";
      title_h.innerHTML = response['title'].bold();
      quote_div.appendChild(title_h);
      var quote_d = document.createElement('div');
      quote_d.className = "w3-border w3-border-gray w3-container";
      var quote_p = document.createElement('p');
      quote_p.innerText = response['quote'];
      quote_d.appendChild(quote_p);
      var auth_p = document.createElement('p');
      auth_p.className = "w3-right-align";
      auth_p.innerText = '- ' + response["author"];
      quote_d.appendChild(auth_p);
      quote_div.appendChild(quote_d);
      var update_d = document.createElement('div');
      update_d.innerText = 'Data Updated: ' + response['datetime'].replace('T', ' ');
      if (response['update_late']) {
        update_d.className = "w3-text-red w3-center";
      } else {
        update_d.className = "w3-center";
      }
      quote_div.appendChild(update_d);
    },
    error: function (xhr, status, error) {
      var icon = document.createElement("i");
      icon.className = "fas fa-exclamation-circle w3-text-red fa-9x";
      quote_div.innerHTML = "";
      quote_div.appendChild(icon);
    },
  });
}

function get_weather(latitude, longitude) {
  var weather_div = document.getElementById("weather_div");
  $.ajax({
    url: "/pidata/weather/",
    method: "GET",
    data: { lat: latitude, lon: longitude },
    global: false,
    success: function (response) {
      console.log(response);
      weather_div.innerHTML = "";
      var status_div = document.createElement("div");
      status_div.className = "w3-center " + response["bg_color"];
      status_div.style.margin = "0 auto";
      status_div.style.maxWidth = "128px";
      var status_img = document.createElement("img");
      status_img.className = "w3-round";
      status_img.alt = response["status"];
      status_img.src = response["icon"];
      status_div.appendChild(status_img);
      weather_div.appendChild(status_div);
      status_div.offsetHeight = status_img.clientWidth;
      var status_heading = document.createElement("h3");
      status_heading.className = "w3-center w3-xlarge";
      status_heading.innerText = response["detailed_status"];
      weather_div.appendChild(status_heading);
      var weather_heading = document.createElement("h1");
      weather_heading.className = "w3-center w3-jumbo";
      temp = parseInt(Math.ceil(response["temp"]["temp"]));
      if (temp <= 50) {
        weather_heading.className += " w3-text-blue";
      } else if (temp > 50 && temp <= 70) {
        weather_heading.className += " w3-text-yellow";
      } else if (temp > 70 && temp <= 80) {
        weather_heading.className += " w3-text-green";
      } else if (temp > 80 && temp <= 90) {
        weather_heading.className += " w3-text-orange";
      } else if (temp > 90) {
        weather_heading.className += " w3-text-red";
      }
      weather_heading.innerText = temp + "\xB0F";
      weather_div.appendChild(weather_heading);
      var feels_heading = document.createElement("h3");
      feels_heading.className = "w3-center w3-xlarge";
      feels_heading.innerText =
        "Feels Like " + parseInt(Math.ceil(response["temp"]["feels_like"])) + "\xB0F";
      weather_div.appendChild(feels_heading);
      create_forecast(response["forecast"], response["bg_color"]);
    },
  });
}

function create_forecast(forecast_data, bg_color) {
  var forecast_div = document.getElementById("forecast_div");
  forecast_div.innerHTML = "";
  for (var i in forecast_data) {
    weather_data = forecast_data[i];
    var w_div = document.createElement('div');
    w_div.className = "w3-small w3-cell w3-center " + bg_color;
    w_div.style.maxWidth = parseInt(forecast_div.clientWidth / 5) + 'px';
    var day_h = document.createElement('h6');
    day_h.innerText = weather_data["day"];
    w_div.appendChild(day_h);
    img = document.createElement("img");
    img.src = weather_data['icon'];
    w_div.appendChild(img);
    var stat_p = document.createElement('p');
    stat_p.innerText = weather_data['status'];
    w_div.appendChild(stat_p);
    var temp_h = document.createElement('h6');
    temp_h.innerHTML = (weather_data["temp_max"] + '\xB0F<br>' + weather_data["temp_min"] + '\xB0F').bold();
    w_div.appendChild(temp_h);
    forecast_div.appendChild(w_div);
  }
}

function get_notifications() {
  var notify_button = document.getElementById("notify_alarm");
  var notify_div = document.getElementById("notifications");
  var notif_count_span = document.getElementById('notif_counts');
  $.ajax({
    url: "/pidata/notifications/",
    method: "GET",
    data: {},
    global: false,
    success: function (response) {
      console.log('Got notifications: ' + response["notifications"].length);
      notif_count_span.innerText = 'Displaying ' + response['displayed'] + ' of ' + response['total'] + ' Notifications';
      if (response["notifications"].length > 0) {
        notify_button.classList.add('w3-text-red');
      } else {
        console.log(notify_button.className);
        notify_button.classList.remove('w3-text-red');
        console.log(notify_button.className);
      }
      notify_div.innerHTML = "";
      for (var i in response["notifications"]) {
        notif_data = response["notifications"][i];
        var div = document.createElement("div");
        div.className = "w3-container w3-row w3-margin";
        div.id = "notif_" + i;
        var l_div = document.createElement("div");
        l_div.className = "w3-cell w3-cell-middle";
        l_div.style.maxWidth = "10%";
        var btn = document.createElement('button');
        btn.className = "w3-btn w3-blue";
        btn.innerHTML = '<i class="fas fa-envelope-open-text fa-2x"></i>';
        btn.onclick = function () {
          clear_notification(notif_data["real_datetime"], notif_data["node"], notif_data["app"]);
        };
        var p = document.createElement("div");
        p.className = "w3-container w3-cell w3-cell-top";
        p.innerHTML = "At: ".bold() + notif_data["display_datetime"] + "<br>From: ".bold() + notif_data["node"] + "." + notif_data["app"] + "<br>Message: ".bold() + notif_data["msg"];
        l_div.appendChild(btn);
        div.appendChild(l_div);
        div.appendChild(p);
        notify_div.appendChild(div);
      }
    },
  });
}

function clear_notification(datetime, node, app) {
  $.ajax({
    url: "/pidata/clear_notification/",
    method: "GET",
    data: { datetime: datetime, node: node, app: app },
    global: false,
    success: function (response) {
      get_notifications();
    },
  });
}

function clear_all_notifications() {
  $.ajax({
    url: "/pidata/clear_all_notifications/",
    method: "GET",
    data: {},
    global: false,
    success: function (response) {
      notify_close();
      get_notifications();
    },
  });
}

function notify_open() {
  document.getElementById("notif_bar").style.display = "block";
  document.getElementById('notify_alarm').onclick = function () { notify_close(); };
}

function notify_close() {
  document.getElementById("notif_bar").style.display = "none";
  document.getElementById('notify_alarm').onclick = function () { notify_open(); };
}

