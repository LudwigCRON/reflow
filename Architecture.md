Dependencies
============
Reflow is a runner and load tools defined either in this
repository, or in a shared drive, or in an HDL project.
Thus there is no predefined exhaustive list of
dependencies.

In consequence, in this section we list only those for
the tools defined in this repository:

- doit: tasks
- tiny-orm: database
- mako: template
- pyyaml: yaml support
- tkinter: gui
- numpy and scipy: analog raw data + series
- matplotlib*: predefine plot style if needed

Matplotlib is not loaded by any tool in the repository.
However, it is useful to plot analog signals for reports
and the quality of default plot is not satisfactory.

To be closer to a publication ready quality, some 
predefined settings can be called in `common.utils.graphs`.

Configuration
=============
Reflow is based on the following strategy: a tool
is a package loaded with a given configuration for a
given version and a list of tasks.

Therefore, there is a configuration file to define
which tool should be loaded `project.yaml`, and a
configuration file inside each tool's folder `config.yaml`.

While a `config.yaml` file is only used inside the package
of the tool concerned, information contained in
`project.yaml` is provided to all tools.

project.yaml
------------
An HDL project is supposed to be identified by a given
unique name. This is given in a specifc section called
`project`.

The section `project` can be further extended depending
on the user policy.

A section `tools` defines the list of tools to be loaded.
It is an array of the name of the folder of a given
package. The lookup path is by default the folder tools
in the installation directory of Reflow, `$REFLOW/tools`.
For the sake of conveniance, the user can specify other
lookup paths via `tools_paths`. This parameter is an array
of lookup path.

In the case a tool called **test** is found in
`$REFLOW/tools`, and in one of the specified 
`tools_paths`, the tool in the installation directory of
Reflow prevail. For an similar tool's name between
two different lookup paths, the first specified prevail.


Reflow infers the command to be run base on the name of the task defined by a tool package.
So the lonely task ending with `_lint` will be executed with a `run lint`.
In case several tasks ending with `_lint` is loaded an error message is given
```
Run have found several handler for 'lint':
- task_iverilog_lint
- task_yosys_lint
- task_verible_lint

Define a bind rule in project.yaml to resolve conflict
```

To resolve the conflict, a `bind` section defines which
task should be called on a given `run` command.

Here is an example of a `project.yaml`
```yaml
project:
  name: fpga_magenda
work_dir_prefix: .tmp
tools:
- iverilog
- yosys
- covered
- verible
tools_paths: # path to lookup for tools
- $PROJECT/tools/
bind:
  lint: task_verible_lint
  synth: task_yosys_synth
```

config.yaml
-----------
This configuration file is tightly linked to the package
of a specific tool. The variables and parameters can vary
from one tool to another.

However, it is commended to specify the at least some
common parameters:

- format: file format selection for dumped waveforms
- flags: common flags to be set by default

A typical `config.yaml` file is
```yaml
format: vcd
flags:
- -g2012
- -grelative-include
- -Wanachronisms
- -Wimplicit
- -Wimplicit-dimensions
- -Wportbind
```

Other parameters used by the tool inside the Reflow
repository should be described by in `config.md`
file alongside inside the folder of the tool.

Architecture
============
For the repository:
- **common:** python files essential to the behaviour of run
- **packages:** extra files usable by several tools
- **envs/bin:** executable callable by the user in a terminal
- **tools:** provided tools supported by Reflow
- **tests:** tests to check the behaviour of Reflow

For each tool there are at least:
- `__init__.py` file defining the tasks to be performed.
- `README.md` describing the supported features and which version of the tool is supported. 

In case a tools have some configuration, it is recommended
to provide at least:
- `config.yaml` to provide simplified edition of parameter
- `config.md` describing the possible configurations
  
Therefore it is common to see the following arborescence
for a given lookup `tools_paths`:
```
tools/
    tool1/
        - __init__.py
        - config.yaml
        - config.md
        - README.md
    tool2/
        - __init__.py
        - config.yaml
        - config.md
        - templates/
        - README.md
    tool3/
        - __init__.py
        - README.md
```

Each task in a tool should be named `task_<toolname>_<name_of_task>` to prevent
any collision

Executable
==========

create
------
This executable is used to create allows one to create
an isolated python environment with Reflow tools included.

It also allows to create a blank project.

run
----
Script reading the `project.yaml`, loading tools,
and executing the specified task.

Database
========
use a sqlite database for task executed by run:
| task_name | cwd | exec_time | elapsed_time | success | score |
| --------- | --- | --------- | ------------ | ------- | ----- |
| str       | str | str       | int          | bool    | float |

for the exec_time the date follows the specified format `yyyy-mm-dd hh:mm:ss`

use a sqlite database for hierarchy and instances information provided for templating engine. The tables are described below

Modules
-------

| name | path | type | is_memory |
| ---- | ---- | ---- | --------- |
| str  | str  | str  | bool      |

the type is one of the following:
- RAM
- ROM
- OTP
- MTP
- NVRAM
- EEPROM
- FLASH
- ADC
- DAC
- CUSTOM

instances
------------

| id  | name | module |
| --- | ---- | ------ |
| int | str  | str    |

:warning: As for most synthesizer and simulator, the name of a module should
be unique, it is reasonnable to assume that module's name are their
identifier.

pins
-----

| name | instance | direction | type | msb | lsb | net | related_pin | cap_load | res_load | access_time | setup_time | hold_time | transition_time | analysis_view |
| ---- | -------- | --------- | ---- | --- | --- | --- | ----------- | -------- | -------- | ----------- | ---------- | --------- | --------------- | ------------- |
| str  | int      | int       | int  | int | int | str | str         | float    | float    | float       | float      | float     | float           | str           |

direction can be either:
- input = 0
- output = 1
- inout = 2

type can be either:
- wire = 0
- reg = 1
- real = 2

cap_load is expressed in Farad, res_load in Ohm, and time information is expressed in second.

analysis_view is the tag assigned for the specific timing and
loading information. This is usually needed for 
multimode-multicorner synthesis. In a more traditional way,
it is expected to read either min, typ, max.

parameters
------------

| instance | name | value |
| -------- | ---- | ----- |
| int      | str  | str   |


Templating
==========

expected templating for a verilog instance with the mako engine is
```mako
% for inst in instances:
    % if inst.params:
    ${inst.module.name} #(
        % for param, value in inst.params:
            .${param}   (${value})${"," if not loop.last else ""}
        % endfor
    ) ${inst.name} (
        % for pin in inst.pins:
        .${pin.name}    (${pin.net})${"," if not loop.last else ""}
        % endfor
    );
    % else:
    ${inst.module.name}  ${inst.name} (
        % for pin in inst.pins:
        .${pin.name}    (${pin.net})${"," if not loop.last else ""}
        % endfor
    );
    % endif

% endfor
```

pins shall be sorted by name by default

parameters shall be sorted by name by default

It should also be possible to do the following
```mako
% for pin in inst.inputs():
    % if pin.width() > 1:
    ${pin.type} [${pin.msb}:${pin.lsb}] ${pin.name};
    % else:
    ${pin.type}                         ${pin.name};
    % endif
% endfor

% for pin in inst.outputs():
    % if pin.width() > 1:
    ${pin.type} [${pin.msb}:${pin.lsb}] ${pin.name};
    % else:
    ${pin.type}                         ${pin.name};
    % endif
% endfor

% for pin in inst.inouts():
    % if pin.width() > 1:
    ${pin.type} [${pin.msb}:${pin.lsb}] ${pin.name}_i;
    ${pin.type} [${pin.msb}:${pin.lsb}] ${pin.name}_o;
    % else:
    ${pin.type}                         ${pin.name}_i;
    ${pin.type}                         ${pin.name}_o;
    % endif
% endfor
```

Project
========

A `top.yaml` describes the hierarchy as the following:
```yaml
...
instance_name:
    module: <module path>
    # instance parameters
    params:
        name: value
        name: value
    # connections
    pins:
        name1: first_net_name
        name2[2:0]: second_net_name[11:9]
...
```

Formulas to compute value is not supported. A custom
configurator, or custom tools should be used and generate
a static final `top.yaml` file.

Configuration
---------------
It should be possible to:
- add a module from a list
- add new search_path for modules (update the list)
- add a new instance
- remove an instance
- edit parameters (table with default value)
- list all pins for an instance
- create default net for connections
- read an existing top.yaml
- save into top.yaml

Each block should provide a `<block_name>_schema.yaml`.
this schema is similar to a json schema. It represents
all possible values for a given parameters and provide
the description of the paramater/signal.

Memory Map & Protection
------------------------
To list all the possible zone, the configurator should read first
the project.yaml and list all memories. Their parameters should contains at list start and size information.

A map of the available memories should be represented.
One can then define zones and their permissions.

| start | size | key | permission |
| ----- | ---- | --- | ---------- |
| int   | int  | int | str        |

a key is associated to each "user". A "user" can be a specific
component in a given mode.

the permission is one of the following:
- "--": a given user cannot read nor write this zone
- "r-": a given user can only read this zone
- "-w": a given user can only write this zone
- "rw": a given user can read and write this zone

:warning: if at least one memory block as been declared in the project.yaml,
a memory protection unit should be generated and automatically
instantiated.