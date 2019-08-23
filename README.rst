====
VOLO
====

An interactive linear optics visualisation GUI, and optimizer.

For documentation refer to ``volo/annotated_window.png``, and the comments and
docstrings in the code.

VOLO is hosted on GitHub, `here <https://github.com/dls-controls/volo>`_

Installation:
-------------

It is easiest to do this using a virtualenv, inside volo:

* ``virtualenv --no-site-packages venv``
* ``source venv/bin/activate``
* ``pip install -r requirements.txt``

The GUI can be run using:

* ``python volo/gui.py``

The optimizer can be run inside an interactive python shell:

* ``python``
* ``>>> import volo.optimizer as o``
* ``>>> constraints = o.Contratints(lattice, constraints_dictonary)``
* ``>>> variables = o.Variables(fields, indices, values)``
* ``>>> optimizer = o.Optimizer(constraints, variables)``
* ``>>> output_lattice = optimizer.run()``

For more comprehensive examples please review ``volo/examples.py``.
