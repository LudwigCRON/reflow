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
                % for block in blocks:
                <tr>
                    <td>{block.name}</td>
                    <td>{block.lint}/{block.nb_lint}</td>
                    <td>{block.simulation}/{block.nb_simulation}</td>
                    <td>{block.coverage}/{block.nb_coverage}</td>
                    <td>{block.total_time}</td>
                </tr>
                % endfor
            </tbody>
        </table>

        % for block in blocks:
        <details>
            <summary>
                {block.name}
            </summary>
            <table>
                <th>
                    <td>id</td>
                    <td>warnings</td>
                    <td>errors</td>
                    <td>total time</td>
                </th>
                <tbody>
                    % for lint in blocks.lints
                    <tr>
                        <td>{lint.id}</td>
                        <td>{lint.warnings}</td>
                        <td>{lint.errors}</td>
                        <td>{lint.total_time}</td>
                    </tr>
                    % endfor
                </tbody>
            </table>
            <table>
                <th>
                    <td>id</td>
                    <td>warnings</td>
                    <td>errors</td>
                    <td>total time</td>
                </th>
                <tbody>
                    % for sim in blocks.sims
                    <tr>
                        <td>{sim.id}</td>
                        <td>{sim.warnings}</td>
                        <td>{sim.errors}</td>
                        <td>{sim.total_time}</td>
                    </tr>
                    % endfor
                </tbody>
            </table>
            <table>
                <th>
                    <td>id</td>
                    <td>warnings</td>
                    <td>errors</td>
                    <td>total time</td>
                </th>
                <tbody>
                    % for cov in blocks.covs
                    <tr>
                        <td>{cov.id}</td>
                        <td>{cov.warnings}</td>
                        <td>{cov.errors}</td>
                        <td>{cov.total_time}</td>
                    </tr>
                    % endfor
                </tbody>
            </table>
        </details>
        % endfor
    </body>
</html>