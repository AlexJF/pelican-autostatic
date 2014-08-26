##################
pelican-autostatic
##################

A plugin for `Pelican
<http://pelican.readthedocs.org/en/latest/>`_ that
adds automatic resolution of static files.

While the original static generator included in Pelican requires the hardcoding
of static paths in the configuration file, pelican-autostatic provides 
facilities to dinamically add static content independent of its location, just
by referencing it.

Install
=======

To install the library, you can use
`pip
<http://www.pip-installer.org/en/latest/>`_

.. code-block:: bash

    $ pip install pelican-autostatic


Usage
=====

1. Update ``pelicanconf.py``:

   1. Add ``pelican-autostatic`` to ``PLUGINS``.
      
      You should add it before any metadata-affecting plugins.

      .. code-block:: python
      
          PLUGINS = ['pelican-autostatic', ...]

2. Reference static content in your Markdown/rST metadata/text by using the
   ``{static}`` substitution: ::

       {static url/to/content key1=val1 key2="val 2" ...}

   or::

       {static "url/to/content/with spaces" key1=val1 key2="val 2" ...}

   Example (in markdown): ::

       [Markdown example file]({static file/example.zip})

3. An index of these references will be automatically built and those files
   will be copied to the output folder preserving the path structure:

   - If using a relative path, the file will be copied to the same path
     relative to the directory where the .html file is output.
   - If using an absolute path, the file is copied to that same path
     relative to the base output folder (e.g: ``output``).

Options
=======
Autostatic references can have a number of options after the url for the
content. This allows modifications to the content being referenced.

Core options
------------

- ``output``: Allows changing the output path (and the url) of the file in
  the generated .html.

  Example: ::

      {static /images/example.png output=/images/example_2.png}

  Will copy ``content/images/example.png`` to ``output/images/example_2.png``
  and the reference will be replaced by ``$SITEURL/images/example_2.png``.

- ``url``: Allows changing the url of the file in the generated .html
  without changing the output path.

  Example: ::

      {static /images/example.png url=/images/example_2.png}

  Will copy ``content/images/example.png`` to ``output/images/example.png``
  and the reference will be replaced by ``$SITEURL/images/example_2.png``.


Third-party options
-------------------

- `pelican-advthumbnailer
  <https://github.com/AlexJF/pelican-advthumbnailer>`_ adds a ``thumb``
  option that changes the url of the static image reference so that a thumbnail
  of that image is generated and linked and not the image itself.


Extending
=========

Available signals
-----------------

- ``autostatic_path_found``: Signalled when a new autostatic reference is found.
  
  Parameters:

  - ``sender``: Always ``None``
  - ``autostatic_path``: Object containing:

    - ``source``: Read-only property containing source path of reference.
    - ``destination``: Read/write property containing destination of 
      referenced file.
    - ``original_destination``: Read-only property containing default
      destination of referenced file.
    - ``url``: Read/write property containing url to be substituted for
      the reference.
    - ``original_url``: Read-only property containing default url to
      be substituted for the reference.
    - ``extra``: Dictionary containing the options specified in addition
      to the path. Can be possibly empty.

`pelican-advthumbnailer
<https://github.com/AlexJF/pelican-advthumbnailer>`_ contains an example
usage of this signal.


Example
=======

For a working example check `my site
<http://www.alexjf.net>`_ and `my site's source code
<https://github.com/AlexJF/alexjf.net>`_.

