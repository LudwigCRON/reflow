<%!
import os
from datetime import datetime

def to_time(str_t_ms):
    t_ms = 0
    if isinstance(str_t_ms, str):
        try:
            t_ms = int(str_t_ms.strip(), 10)
        except ValueError:
            pass
    else:
        t_ms = str_t_ms
    if t_ms is None:
        return "-"
    hours = t_ms//3600000
    minutes = (t_ms - hours * 3600000) // 60000
    seconds = (t_ms % 60000) // 1000
    ms = t_ms % 1000
    if hours > 0:
        return "%dh%dm%d.%ds" % (hours, minutes, seconds, ms)
    elif minutes > 0:
        return "%dm%d.%ds" % (minutes, seconds, ms)
    else:
        return "%d.%ds" % (seconds, ms)


def get_block_name(block: dict):
    if block is None:
        return ''
    return block.get('name', '')
%>
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        :root,
        html {
            font-family: Lato, Arial, Helvetica;
        }

        summary {
            margin: 0;
            padding: 0.125rem 1rem;
            background: #65BBA9;
            color: #FFF;
            font-size: 1.125rem;
            text-transform: uppercase;
        }

        details {
            margin: 1rem 0;
            padding: 0;
        }

        details h3 {
            padding: 0.125rem;
            background: #CCC;
            font-size: 1rem;
        }

        details h3~* {
            margin-bottom: 1rem;
        }

        details h3:not(:first-child) {
            margin: 0;
        }

        table {
            border-collapse: collapse;
            width: 100%
        }

        thead,
        th {
            background: #CCC;
            border: 0;
        }

        tr:nth-child(2n+1) {
            background: #EEE;
        }

        td:first-child {
            text-align: left;
            padding-left: 1em;
        }

        td {
            text-align: center;
        }
    </style>
    <script>
        document.addEventListener("readystatechange", function() {
            if (document.readyState === "complete") {
                var expand_all_btn = document.querySelector("#expand_all_btn");
                expand_all_btn.addEventListener("click", function() {
                    let details = document.querySelectorAll("details");
                    for(let i = 0; i < details.length; i++) {
                        details[i].setAttribute("open", "true");
                    }
                }, true);

                var close_all_btn = document.querySelector("#close_all_btn");
                close_all_btn.addEventListener("click", function() {
                    let details = document.querySelectorAll("details");
                    for(let i = 0; i < details.length; i++) {
                        details[i].removeAttribute("open");
                    }
                }, true);
            }
        }, true);
    </script>
</head>

<body>
    <% sblocks = sorted(blocks, key=get_block_name) %>
    <h1>${os.path.basename(os.getcwd())}</h1>
    <h2>${datetime.now().strftime("%A, %d. %B %Y %H:%M")}</h2>
    <p>
        <em>Errors:</em>${"%d" % sum((b.get("errors", 0) for b in blocks))}
        <br>
        <em>Warnings:</em>${"%d" % sum((b.get("warnings", 0) for b in blocks))}
        <br>
        <em>Elapsed Time:</em>${to_time(sum((b.get("total_time", 0) for b in blocks)))}
    </p>
    <button id="expand_all_btn">Expand All</button>
    <button id="close_all_btn">Close All</button>
    <table>
        <thead>
            <th>name</th>
            <th>lint</th>
            <th>simulation</th>
            <th>coverage</th>
            <th>total time</th>
        </thead>
        <tbody>
            % for i, block in enumerate(sblocks):
            <tr>
                <td>
                    <a href="#${block.get('name')}">
                        ${block.get("name")}
                    </a>
                </td>
                % if block.get("nb_lint"):
                <td>${"%d" % block.get("lint")}/${"%d" % block.get("nb_lint")}</td>
                % else:
                <td>-</td>
                % endif
                % if block.get("nb_simulation"):
                <td>${"%d" % block.get("simulation")}/${"%d" % block.get("nb_simulation")}</td>
                % else:
                <td>-</td>
                % endif
                % if block.get("nb_coverage"):
                <td>${"%d" % block.get("coverage")}/${"%d" % block.get("nb_coverage")}</td>
                % else:
                <td>-</td>
                % endif
                <td>${to_time(block.get("total_time"))}</td>
            </tr>
            % endfor
        </tbody>
    </table>

    % for i, block in enumerate(sblocks):
    <details id="${block.get('name')}">
        <summary>
            ${block.get("name")}
        </summary>
        <h3>Lint</h3>
        % if not block.get("lints", []):
        <div class="warnings">No lints</div>
        % else:
        <table>
            <thead>
                <th>id</th>
                <th>warnings</th>
                <th>errors</th>
                <th>total time</th>
            </thead>
            <tbody>
                % for i, lint in enumerate(block.get("lints", [])):
                <tr>
                    <td>${lint.get("name")}</td>
                    <td>${"%d" % lint.get("warnings")}</td>
                    <td>${"%d" % lint.get("errors")}</td>
                    <td>${lint.get("total_time")}</td>
                </tr>
                % endfor
            </tbody>
        </table>
        % endif

        <h3>Simulation</h3>
        % if not block.get("sims", []):
        <div class="warnings">No simulations</div>
        % else:
        <table>
            <thead>
                <th>id</th>
                <th>warnings</th>
                <th>errors</th>
                <th>total time</th>
            </thead>
            <tbody>
                % for i, sim in enumerate(block.get("sims", [])):
                <tr>
                    <td>${sim.get("name")}</td>
                    <td>${"%d" % sim.get("warnings")}</td>
                    <td>${"%d" % sim.get("errors")}</td>
                    <td>${to_time(sim.get("total_time"))}</td>
                </tr>
                % endfor
            </tbody>
        </table>
        % endif

        <h3>Code coverage</h3>
        % if not block.get("covs", []):
        <div class="warnings">No coverage simulations</div>
        % else:
        <table>
            <thead>
                <th>id</th>
                <th>warnings</th>
                <th>errors</th>
                <th>total time</th>
            </thead>
            <tbody>
                % for i, cov in enumerate(block.get("covs", [])):
                <tr>
                    <td>${cov.get("name")}</td>
                    <td>${"%d" % cov.get("warnings")}</td>
                    <td>${"%d" % cov.get("errors")}</td>
                    <td>${to_time(cov.get("total_time"))}</td>
                </tr>
                % endfor
            </tbody>
        </table>
        % endif
    </details>
    % endfor
</body>

</html>