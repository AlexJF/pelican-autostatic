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

   1. Add ``autostatic`` to ``PLUGINS``.
      
      You should add it before any metadata-affecting plugins.

      .. code-block:: python
      
          PLUGINS = ['autostatic', ...]

2. Reference static content in your Markdown/rST metadata/text by using the
   ``{static}`` substitution: ::

       {static url/to/content key1=val1 key2="val 2" ...}

   or::

       {static "url/to/content/with spaces" key1=val1 key2="val 2" ...}

   Example (in markdown): ::

       [Markdown example file]({static file/example.zip key1=val1 key2="val 2" ...})

   You can also use ``|`` instead of spaces if you wish (for use with Markdown 
   inline image syntax which doesn't accept spaces for the url for instance): ::

       ![Markdown example image]({static|file/example.png|key1=val1} "Image title")

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


Configuration
=============
You can set the following options in your ``pelicanconf.py``:

- ``AUTOSTATIC_REFERENCE_PATTERN`` (String) - Change the regex of the static reference 
  pattern. It needs to have the following groups:

  - ``path`` - This should have the path used in the reference.
  - ``extra`` - This should have the ``key1=val1 key2="val 2" ...`` string.

  For reference, the default pattern is: ::

      r"""{static(?:\s+|\|)((?:"|')?)(?P<path>[^\1=]+?)\1(?:(?:\s+|\|)(?P<extra>.*))?\s*}"""

- ``AUTOSTATIC_USE_PELICANLIKE_REF`` (Boolean) - Activate the usage of a different format of
  the static reference that is similar to `Pelican's {filename} syntax
  <http://docs.getpelican.com/en/3.4.0/content.html#linking-to-internal-content>`_: ::

      ![Markdown example image]({static|key1=val1}images/example.png "Image title")

  *NOTE:* I haven't actually benchmarked this but this mechanism (the same used
  by Pelican with ``{filename}``) should be slightly slower than the default one
  used in this plugin. This is because the ``{filename}`` mechanism does
  matching over all html tags which will surely result in a lot of backtracks
  on a HTML document.


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

