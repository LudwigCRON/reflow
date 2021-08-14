<%
import os
from datetime import datetime
%>\
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        /* color palette from https://coolors.co/ef476f-ffd166-06d6a0-118ab2-073b4c*/

        @import url('https://fonts.googleapis.com/css2?family=Zilla+Slab:wght@600&display=swap');


        /* zilla-slab-700 - latin */
        @import url('https://fonts.googleapis.com/css2?family=Zilla+Slab:wght@600&display=swap');

        :root,
        html {
            font-family: Lato, Arial, Helvetica;
            color: #073b4c;
            --text: #073B4C;
            --header-bg: #073B4C;
            --header-fg: #FFF;
            --extra-bg: #073B4C33;
            --tbl-header-bg: #118AB2;
            --tbl-header-fg: #FFF;
            --healthy-bg: #06D6A0;
            --caution-bg: #FFD166;
            --alarm-bg: #EF476F;
            box-sizing: border-box;
            max-width: 1200px;
            margin: 0 auto;
        }

        @media print {
            html {
                max-width: 100%;
            }
        }

        *, *:before, *:after {
            box-sizing: inherit;
            margin: 0;
            padding: 0;
        }

        h1, h2 {
            font-family:  'Zilla Slab', "Palatino Linotype",serif;
            letter-spacing: .035rem;
            line-height: 1.2;
            margin-bottom: 0.5rem;
        }

        button {
            background: var(--header-bg);
            color: #fff;
            border-radius: 4px;
            padding: 0.125rem 1rem;
            margin: 0.125rem 1rem;
        }

        body > table {
            margin: 0 1rem;
            width: calc(100% - 2rem);
        }

        /* ==== accordeons ==== */
        .test_group {
            background: var(--extra-bg);
            margin: 1rem;
            padding: 0 1rem;
            border-radius: 6px;
            overflow: hidden;
        }

        .test_group[open] {
            padding: 0 1rem 1rem 1rem;
        }

        .test_group[open] .test_group-header {
            margin: 0 0 1rem -1rem;
        }

        .test_group-header {
            background: var(--header-bg);
            color: var(--header-fg);
            padding: 0.25rem 1rem;
            width: 100%;
            margin: 0 0 0 -1rem;
        }

        .test_group-title {
            display: inline;
            margin: 0;
            padding: 0.125rem 1rem;
            font-size: 1.125rem;
            text-transform: uppercase;
        }

        .test_group-section-title {
            margin: 0;
            padding: 0.125rem;
            font-size: 1rem;
        }

        .test_group-section-title:not(:first-of-type) {
            margin-top: 1rem;
        }

        /* ==== tables ==== */
        table {
            border-collapse: collapse;
            width: 100%;
            border-radius: 6px;
            overflow: hidden;
        }

        thead {
            background: var(--tbl-header-bg);
            color: var(--tbl-header-fg);
            border: 0;
            border-bottom: 3px solid var(--header-bg);
        }

        thead th {
            background: var(--tbl-header-bg);
        }

        th, tr {
            height: 1.5rem;
            border: 1px solid #ccc;
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

        .sanity-none {
            color: transparent;
        }
        .sanity-bad {
            background: var(--alarm-bg);
            color: #fff;
        }
        .sanity-caution {
            background: var(--caution-bg);
            color: #fff;
        }
        .sanity-healthy {
            background: var(--healthy-bg);
            color: #fff;
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
    <h1>${os.path.basename(os.getcwd())}</h1>
    <h2>${datetime.now().strftime("%A, %d. %B %Y %H:%M")}</h2>
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
            % for test_path in get_groups(db.__dict__):
            <% 
                prefix = test_path.split("/", 2)[0] if "/" in test_path else test_path
                def select_task(task_name: str):
                    def _(t):
                        return t == task_name
                    return _
                
                def no_rule_flagged(t):
                    if t is None:
                        return True
                    return t == 0

                def count_filtered(prefix: str, filters: dict) -> int:
                    return len(list(filter_task(prefix, filters)))
                
                def sanity_class(valid: int, total: int = 100):
                    if total <= 0:
                        return "none"
                    if valid/total > 0.99:
                        return "healthy"
                    if valid/total > 0.95:
                        return "caution"
                    return "bad"
                    
                
                nb_total_lint = count_filtered(prefix, {"task_name": select_task("lint")})
                nb_total_sim = count_filtered(prefix, {"task_name": select_task("sim")})
                nb_total_cov = count_filtered(prefix, {"task_name": select_task("cov")})
                nb_valid_lint = count_filtered(prefix, {"task_name": select_task("lint"), "ERROR": no_rule_flagged, "FATAL": no_rule_flagged})
                nb_valid_sim = count_filtered(prefix, {"task_name": select_task("sim"), "ERROR": no_rule_flagged, "FATAL": no_rule_flagged})
                nb_valid_cov = count_filtered(prefix, {"task_name": select_task("cov"), "ERROR": no_rule_flagged, "FATAL": no_rule_flagged})
            %>\
            <tr>
                <td>
                    <a href="#${prefix}">
                        ${prefix}
                    </a>
                </td>
                <td class="sanity-${sanity_class(nb_valid_lint, nb_total_lint)}">${nb_valid_lint}/${nb_total_lint}</td>
                <td class="sanity-${sanity_class(nb_valid_sim, nb_total_sim)}">${nb_valid_sim}/${nb_total_sim}</td>
                <td class="sanity-${sanity_class(nb_valid_cov, nb_total_cov)}">${nb_valid_cov}/${nb_total_cov}</td>
                <td>-</td>
            </tr>
            % endfor
        </tbody>
    </table>
    % for test_path, variants in get_groups(db.__dict__).items():
    <details class="test_group">
    <summary class="test_group-header">
    <h2 class="test_group-title">${test_path}</h2>
    </summary>
    <h3 class="test_group-section-title">lint</h3>
    % if count_filtered(test_path, {"task_name": select_task("lint")}):
    <table>
        <thead>
            <th></th>
            <th>Warnings</th>
            <th>Errors</th>
            <th>Elapsed Time</th>
        </thead>
        % for variant, tasks in variants.items():
            % for task in tasks:
                % if task.task_name == "lint":
        <tr>
            <td>${variant}</td>
            <td class="sanity-${sanity_class(97 if task.get('WARNING', 0) else 100)}">${task.get("WARNING", 0)}</td>
            <td class="sanity-${sanity_class(0 if task.get('ERROR', 0)+task.get('FATAL', 0) else 100)}">${task.get("ERROR", 0)+task.get("FATAL", 0)}</td>
            <td class="${' '.join(['aborted' if task.aborted else '', 'skipped' if task.skipped else ''])}">${task.elapsed_time}</td>
        </tr>
                % endif
            % endfor
        % endfor
    </table>
    % else:
    No Linting
    % endif
    <h3 class="test_group-section-title">simulation</h3>
    % if count_filtered(test_path, {"task_name": select_task("sim")}):
    <table>
        <thead>
            <th></th>
            <th>Warnings</th>
            <th>Errors</th>
            <th>Elapsed Time</th>
        </thead>
        % for variant, tasks in variants.items():
            % for task in tasks:
                % if task.task_name == "sim":
        <tr>
            <td>${variant}</td>
            <td class="sanity-${sanity_class(97 if task.get('WARNING', 0) else 100)}">${task.get("WARNING", 0)}</td>
            <td class="sanity-${sanity_class(0 if task.get('ERROR', 0)+task.get('FATAL', 0) else 100)}">${task.get("ERROR", 0)+task.get("FATAL", 0)}</td>
            <td class="${' '.join(['aborted' if task.aborted else '', 'skipped' if task.skipped else ''])}">${task.elapsed_time}</td>
        </tr>
                % endif
            % endfor
        % endfor
    </table>
    % else:
    No Simulations
    % endif
    <h3 class="test_group-section-title">code coverage</h3>
    % if count_filtered(test_path, {"task_name": select_task("cov")}):
    <table>
        <thead>
            <th></th>
            <th>Warnings</th>
            <th>Errors</th>
            <th>Elapsed Time</th>
        </thead>
        % for variant, tasks in variants.items():
            % for task in tasks:
                % if task.task_name == "cov":
        <tr>
            <td>${variant}</td>
            <td class="sanity-${sanity_class(97 if task.get('WARNING', 0) else 100)}">${task.get("WARNING", 0)}</td>
            <td class="sanity-${sanity_class(0 if task.get('ERROR', 0)+task.get('FATAL', 0) else 100)}">${task.get("ERROR", 0)+task.get("FATAL", 0)}</td>
            <td class="${' '.join(['aborted' if task.aborted else '', 'skipped' if task.skipped else ''])}">${task.elapsed_time}</td>
        </tr>
                % endif
            % endfor
        % endfor
    </table>
    % else:
    No Code coverage
    % endif
    </details>
    % endfor
</body>

</html>