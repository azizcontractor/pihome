function load_solar_data() {
    var solar_div = document.getElementById("solar_data");
    $.ajax({
        url: "/info/solar/",
        method: "GET",
        data: {},
        global: false,
        success: function (response) {
            console.log(response);
            var power_data = response["power"];
            var energy_data = response["energy"];
            solar_div.innerHTML = "";
            var data_row = document.createElement("div");
            data_row.className = "w3-cell-row";
            create_solar_status(data_row, power_data, energy_data);
            create_battery_status(data_row, power_data);
            create_stats(data_row, power_data, energy_data);
            solar_div.appendChild(data_row);
            var h = document.createElement("h6");
            h.className = "w3-center";
            h.innerText = "Data Updated: " + power_data["datetime"].replace("T", " ");
            if (response["update_late"]) {
                h.className += " w3-text-red";
            }
            solar_div.appendChild(h);
        },
        error: function (xhr, status, error) {
            solar_div.innerHTML = "";
            var icon = document.createElement("i");
            icon.className = "fas fa-exclamation-circle w3-text-red fa-9x";
            solar_div.appendChild(icon);
            var h = document.createElement("h3");
            h.innerText = "Could not fetch solar data";
            solar_div.appendChild(h);
        },
    });
}

function create_solar_status(data_row, power_data, energy_data) {
    var solar_status_div = document.createElement("div");
    solar_status_div.className = "w3-cell w3-card-black w3-center w3-cell-top";
    var icon = document.createElement("i");
    icon.className = "fas fa-solar-panel fa-7x";
    if (power_data["solar_status"] == "Active") {
        icon.className += " w3-text-orange";
    } else {
        icon.className += " w3-text-blue";
    }
    solar_status_div.appendChild(icon);
    var energy_h = document.createElement("h3");
    energy_h.className = "w3-center";
    energy_h.innerText = "Total: " + (energy_data["production"] / 1000).toFixed(1) + "kWh";
    solar_status_div.appendChild(energy_h);
    var power_h = document.createElement("h3");
    power_h.className = "w3-center";
    power_h.innerText = "Current: " + power_data["solar_power"].toFixed(2) + "kW";
    solar_status_div.appendChild(power_h);
    data_row.appendChild(solar_status_div);
}

function create_battery_status(data_row, power_data) {
    var battery_status_div = document.createElement("div");
    battery_status_div.className = "w3-cell w3-card-black w3-center w3-cell-top";
    var icon = document.createElement("i");
    if (power_data["battery_critical"]) {
        icon.className = "fas fa-battery-full fa-7x w3-text-red";
    } else if (power_data["battery_charge"] >= 95) {
        icon.className = "fas fa-battery-full fa-7x w3-text-green";
    } else if (power_data["battery_charge"] >= 75) {
        icon.className = "fas fa-battery-three-quarters fa-7x w3-text-yellow";
    } else if (power_data["battery_charge"] >= 50) {
        icon.className = "fas fa-battery-half fa-7x w3-text-yellow";
    } else if (power_data["battery_charge"] >= 25) {
        icon.className = "fas fa-battery-quarter fa-7x w3-text-red";
    } else {
        icon.className = "fas fa-battery-empty fa-7x w3-text-red";
    }
    battery_status_div.appendChild(icon);
    var charge_h = document.createElement("h3");
    charge_h.className = "w3-center";
    charge_h.innerText = "Charge: " + power_data["battery_charge"] + "%";
    battery_status_div.appendChild(charge_h);
    var status_h = document.createElement("h3");
    status_h.className = "w3-center";
    status_h.innerText = "Status: " + power_data["battery_status"];
    battery_status_div.appendChild(status_h);
    data_row.appendChild(battery_status_div);
}

function create_stats(data_row, power_data, energy_data) {
    var stats_div = document.createElement("div");
    stats_div.className = "w3-cell w3-card-black w3-center w3-cell-middle";
    var prod_h = document.createElement("h6");
    prod_h.className = "w3-center";
    prod_h.innerText = "Production: " + (energy_data["production"] / 1000).toFixed(2) + " kWh";
    stats_div.appendChild(prod_h);
    var usage_h = document.createElement("h6");
    usage_h.className = "w3-center";
    usage_h.innerText = "Usage: " + (energy_data["consumption"] / 1000).toFixed(2) + " kWh";
    stats_div.appendChild(usage_h);
    var net_h = document.createElement("h6");
    net_h.className = "w3-center";
    net_h.innerText = "Net: " + ((energy_data["export"] - energy_data["import"]) / 1000).toFixed(2) + " kWh";
    stats_div.appendChild(net_h);
    var current_h = document.createElement("h6");
    current_h.className = "w3-center";
    var span = document.createElement("span");
    if (power_data["grid_status"] == "Active") {
        if (power_data["power_usage"] >= power_data["solar_power"]) {
            current_h.innerText = "Current Status: " + power_data["grid_power"].toFixed(2) + " kW from GRID";
            span.innerHTML = '<i class="fas fa-home"></i>&nbsp;<i class="fas fa-long-arrow-alt-left"></i>&nbsp;<i class="fas fa-broadcast-tower"></i>';
        } else {
            current_h.innerText = "Current Status: " + power_data["grid_power"].toFixed(2) + " kW to GRID";
            span.innerHTML = '<i class="fas fa-home"></i>&nbsp;<i class="fas fa-long-arrow-alt-right"></i>&nbsp;<i class="fas fa-broadcast-tower"></i>';
        }
    } else if (power_data["battery_status"] == "Active" && power_data["grid_status"] != "Active") {
        current_h.innerText = "Current Status: Battery ";
        span.innerHTML = '<i class="fas fa-home"></i>&nbsp;<i class="fas fa-long-arrow-alt-left"></i>&nbsp;<i class="fas fa-battery-half"></i>';
    } else if (power_data["grid_status"] != "Active") {
        current_h.innerText = "Current Status: Powerloss.";
        span.innerHTML = '<i class="fas fa-home"></i>&nbsp;<i class="fas fa-times"></i>';
    }
    stats_div.appendChild(current_h);
    stats_div.appendChild(span);
    data_row.appendChild(stats_div);
}

function load_sensor_data() {
    var sensor_div = document.getElementById("sensor_data");
    $.ajax({
        url: "/info/sensor/",
        method: "GET",
        data: {},
        global: false,
        success: function (response) {
            console.log(response);
            sensor_div.innerHTML = "";
            var data_row = document.createElement("div");
            data_row.className = "w3-cell-row";
            sensor_div.appendChild(data_row);
            create_sensor_stats(data_row, response);
        },
        error: function (xhr, status, error) {
            sensor_div.innerHTML = "";
            var icon = document.createElement("i");
            icon.className = "fas fa-exclamation-circle w3-text-red fa-9x";
            sensor_div.appendChild(icon);
            var h = document.createElement("h3");
            h.innerText = "Could not fetch sensor data";
            sensor_div.appendChild(h);
        },
    });
}

function create_sensor_stats(data_row, sensor_data) {
    for (var location in sensor_data) {
        var loc_div = document.createElement("div");
        loc_div.className = "w3-cell w3-card-black w3-center";
        var loc_h = document.createElement("h2");
        loc_h.className = "w3-center";
        loc_h.innerText = location;
        loc_div.appendChild(loc_h);
        var icon = document.createElement("i");
        icon.className = sensor_data[location]["icon-class"];
        loc_div.appendChild(icon);
        temp = sensor_data[location]["temperature"];
        if (temp <= 50) {
            icon.className += " w3-text-blue";
        } else if (temp > 50 && temp <= 70) {
            icon.className += " w3-text-yellow";
        } else if (temp > 70 && temp <= 80) {
            icon.className += " w3-text-green";
        } else if (temp > 80 && temp <= 90) {
            icon.className += " w3-text-orange";
        } else if (temp > 90) {
            icon.className += " w3-text-red";
        }
        var temp_h = document.createElement("h4");
        temp_h.className = "w3-center";
        temp_h.innerText = "Temperature: " + temp.toFixed(1) + "\xB0F";
        loc_div.appendChild(temp_h);
        var humid_h = document.createElement("h4");
        humid_h.className = "w3-center";
        humid_h.innerText = "Humidity: " + sensor_data[location]["humidity"].toFixed(1) + "%";
        loc_div.appendChild(humid_h);
        var update_h = document.createElement("h4");
        update_h.innerText = "Updated: " + sensor_data[location]["updated"].replace("T", " ");
        if (sensor_data[location]['update_late']) {
            update_h.className += " w3-text-red";
        }
        loc_div.appendChild(update_h);
        data_row.appendChild(loc_div);
    }
}

function load_network_data() {
    var network_div = document.getElementById("network_data");
    $.ajax({
        url: "/info/network/",
        method: "GET",
        data: {},
        global: false,
        success: function (response) {
            console.log(response);
            network_div.innerHTML = "";
            var data_row = document.createElement("div");
            data_row.className = "w3-cell-row";
            network_div.appendChild(data_row);
            create_network_stats(data_row, response);
        },
        error: function (xhr, status, error) {
            network_div.innerHTML = "";
            var icon = document.createElement("i");
            icon.className = "fas fa-exclamation-circle w3-text-red fa-9x";
            network_div.appendChild(icon);
            var h = document.createElement("h3");
            h.innerText = "Could not fetch network data";
            network_div.appendChild(h);
        },
    });
}

function create_network_stats(data_row, network_data) {
    var wan_div = document.createElement("div");
    wan_div.className = "w3-cell w3-card-black w3-center";
    var pihole_h = document.createElement("h2");
    pihole_h.className = "w3-center";
    pihole_h.innerText = 'Network';
    wan_div.appendChild(pihole_h);
    var icon = document.createElement("i");
    icon.className = network_data['wan_icon'];
    wan_div.appendChild(icon);
    var status_h = document.createElement("h4");
    status_h.className = "w3-center";
    status_h.innerText = "Status: " + network_data['wan_status'];
    wan_div.appendChild(status_h);
    var ip_h = document.createElement('h4');
    ip_h.className = "w3-center";
    ip_h.innerText = 'IP: ' + network_data['ip'];
    wan_div.appendChild(ip_h);
    data_row.appendChild(wan_div);
    for (var pihole in network_data['piholes']) {
        var pihole_div = document.createElement("div");
        pihole_div.className = "w3-cell w3-card-black w3-center";
        var pihole_h = document.createElement("h2");
        pihole_h.className = "w3-center";
        pihole_h.innerText = pihole;
        pihole_div.appendChild(pihole_h);
        var icon = document.createElement("i");
        icon.className = network_data['piholes'][pihole]["icon"];
        pihole_div.appendChild(icon);
        var status_h = document.createElement("h4");
        status_h.className = "w3-center";
        status_h.innerText = "Status: " + network_data['piholes'][pihole]['status'];
        pihole_div.appendChild(status_h);
        var ads_h = document.createElement('h4');
        ads_h.className = 'w3-center';
        ads_h.innerText = 'Queries Blocked: ' + network_data['piholes'][pihole]['ads'] + '%';
        pihole_div.appendChild(ads_h);
        data_row.appendChild(pihole_div);
    }
}