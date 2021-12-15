function load_stats() {
    $.ajax({
        url: "/system/stats",
        method: "GET",
        data: {},
        global: false,
        success: function (response) {
            console.log(response);
            for (var node in response) {
                var div = document.getElementById(node + '_data');
                div.innerHTML = "";
                var h = document.createElement('h3');
                h.innerText = node;
                div.appendChild(h);
                var table = document.createElement('table');
                table.className = "w3-table-all w3-margin-bottom";
                for (const [key, value] of Object.entries(response[node])) {
                    if (key != 'updated' && key != 'update_late') {
                        var tr = document.createElement('tr');
                        var th = document.createElement('th');
                        th.className = "w3-black";
                        th.innerText = key;
                        var td = document.createElement('td');
                        td.className = 'w3-black';
                        td.innerText = value;
                        tr.appendChild(th);
                        tr.appendChild(td);
                        table.appendChild(tr);
                    }
                }
                div.appendChild(table);
                var span = document.createElement('span');
                span.innerText = 'Updated: ' + response[node]['updated'].replace('T', ' ');
                if (response[node]['update_late']) {
                    span.classList.add('w3-text-red');
                }
                div.appendChild(span);
            }
        },
        error: function (xhr, status, error) {
            let div_ids = ['sensor1_data', 'sensor2_data', 'sensor3_data', 'displaynode_data', 'mainnode_data'];
            for (const div_id of div_ids) {
                div = document.getElementById(div_id);
                var icon = document.createElement("i");
                icon.className = "fas fa-exclamation-circle w3-text-red fa-7x";
                div.appendChild(icon);
                var h = document.createElement("h3");
                h.innerText = "Could not fetch network data";
                div.appendChild(h);
            }
        },
    });
}