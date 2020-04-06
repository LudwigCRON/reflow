<!DOCTYPE html>
<html>
    <head>

    </head>
    <body>
        <table>
            <th>
                <td>name</td>
                <td>lint</td>
                <td>simulation</td>
                <td>coverage</td>
                <td>total time</td>
            </th>
            <tbody>
                % for i, block in enumerate(blocks):
                <tr>
                    <td>${block.get("name")}</td>
                    <td>${block.get("lint")}/${block.get("nb_lint")}</td>
                    <td>${block.get("simulation")}/${block.get("nb_simulation")}</td>
                    <td>${block.get("coverage")}/${block.get("nb_coverage")}</td>
                    <td>${block.get("total_time")}</td>
                </tr>
                % endfor
            </tbody>
        </table>

        % for i, block in enumerate(blocks):
        <details>
            <summary>
                ${block.get("name")}
            </summary>
            <h3>Lint</h3>
            <table>
                <th>
                    <td>id</td>
                    <td>warnings</td>
                    <td>errors</td>
                    <td>total time</td>
                </th>
                <tbody>
                    % for i, lint in enumerate(block.get("lints", [])):
                    <tr>
                        <td>${lint.get("name")}</td>
                        <td>${lint.get("warnings")}</td>
                        <td>${lint.get("errors")}</td>
                        <td>${lint.get("total_time")}</td>
                    </tr>
                    % endfor
                </tbody>
            </table>
            <h3>Simulation</h3>
            <table>
                <th>
                    <td>id</td>
                    <td>warnings</td>
                    <td>errors</td>
                    <td>total time</td>
                </th>
                <tbody>
                    % for i, sim in enumerate(block.get("sims", [])):
                    <tr>
                        <td>${sim.get("name")}</td>
                        <td>${sim.get("warnings")}</td>
                        <td>${sim.get("errors")}</td>
                        <td>${sim.get("total_time")}</td>
                    </tr>
                    % endfor
                </tbody>
            </table>
            <h3>Code coverage</h3>
            <table>
                <th>
                    <td>id</td>
                    <td>warnings</td>
                    <td>errors</td>
                    <td>total time</td>
                </th>
                <tbody>
                    % for i, cov in enumerate(block.get("covs", [])):
                    <tr>
                        <td>${cov.get("name")}</td>
                        <td>${cov.get("warnings")}</td>
                        <td>${cov.get("errors")}</td>
                        <td>${cov.get("total_time")}</td>
                    </tr>
                    % endfor
                </tbody>
            </table>
        </details>
        % endfor
    </body>
</html>