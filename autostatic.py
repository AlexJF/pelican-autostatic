#!/usr/bin/env python
# encoding: utf-8

import logging
import os
import re
import shutil

# For html escaping/unescaping
import html.parser as HTMLParser
from html import escape as html_escape

from blinker import signal

from pelican import signals, generators
from pelican.contents import Static
from pelican.utils import mkdir_p, get_relative_path

logger = logging.getLogger(__name__)
html_parser = HTMLParser.HTMLParser()

autostatic_generator = None
detected_autostatic_paths = {}

autostatic_path_found = signal("autostatic_path_found")

CUSTOM_STATIC_REF_PATTERN_KEY = "AUTOSTATIC_REFERENCE_PATTERN"
USE_PELICAN_LIKE_REF_KEY = "AUTOSTATIC_USE_PELICANLIKE_REF"

# Works everywhere
DEFAULT_STATIC_REF_PATTERN = r"""{static(?:\s+|\|)((?:"|'|&quot;|&apos;|&#34;|&#39;)?)(?P<path>.+?)\1(?:(?:\s+|\|)(?P<extra>.*))?\s*}"""

# Works just in url-value attributes
PELICAN_LIKE_REF_TAG = r"""{static(?:(?:\s+|\|)(?P<extra>.*))?}"""
PELICAN_LIKE_HREF_PATTERN = r"""
    (?P<markup><\s*[^\>]*  # match tag with all url-value attributes
        (?:href|src|poster|data|cite|formaction|action)\s*=)

    (?P<quote>["\'])      # require value to be quoted
    (?P<ref>{0}(?P<path>.*?))  # the url value
    \2""".format(
    PELICAN_LIKE_REF_TAG
)


def html_unescape(text):
    if text is None:
        return text

    return html_parser.unescape(text)


def parse_static_references(instance, text):
    def _get_static_path(match_obj):
        path = match_obj.group("path")
        extra = html_unescape(match_obj.group("extra"))
        extra_dict = {}
        instance_destination_dir = os.path.dirname(instance.save_as)
        relative_path = False
        using_relative_urls = instance._context.get("RELATIVE_URLS")

        if extra:
            for match in re.finditer(
                r'(\w+)="?((?:(?<!")[^\s|]+|(?<=")(?:\\.|[^"\\])*(?=")))"?', extra
            ):
                extra_dict[match.group(1)] = match.group(2)

        if path.startswith("/"):
            source_path = path[1:]
            destination_path = source_path
            relative_path = False
        else:
            source_path = instance.get_relative_source_path(
                os.path.join(instance.relative_dir, path)
            )
            destination_path = os.path.join(instance_destination_dir, path)
            relative_path = True

        if "output" in extra_dict:
            output_override = extra_dict["output"]

            if output_override.startswith("/"):
                destination_path = output_override[1:]
                relative_path = False
            else:
                destination_path = os.path.join(
                    instance_destination_dir, output_override
                )
                relative_path = True

        if using_relative_urls:
            siteurl = get_relative_path(instance.save_as)
        else:
            siteurl = instance._context.get("localsiteurl", "")

        if relative_path and using_relative_urls:
            url = os.path.relpath(destination_path, instance_destination_dir)
        else:
            url = siteurl + "/" + destination_path

        if "url" in extra_dict:
            url_override = extra_dict["url"]

            if url_override.startswith("/"):
                url = siteurl + url_override
            else:
                url = url_override

                if not using_relative_urls:
                    url = siteurl + "/" + os.path.dirname(instance.save_as) + "/" + url

        url = url.replace("\\", "/")  # for Windows paths.

        static_path_obj = StaticPath(source_path, destination_path, url, extra_dict)
        autostatic_path_found.send(autostatic_path=static_path_obj)

        logger.debug(
            "Detected autostatic path: {} -> {} ({})".format(
                static_path_obj.source, static_path_obj.destination, static_path_obj.url
            )
        )

        detected_autostatic_paths[static_path_obj.destination] = static_path_obj.source

        return html_escape(static_path_obj.url)

    def _parse_pelican_like_reference(m):
        return "".join(
            (m.group("markup"), m.group("quote"), _get_static_path(m), m.group("quote"))
        )

    if text is None:
        return text

    if isinstance(text, str):
        settings = instance.settings

        static_ref_re_pattern = DEFAULT_STATIC_REF_PATTERN

        if settings and CUSTOM_STATIC_REF_PATTERN_KEY in settings:
            static_ref_re_pattern = settings[CUSTOM_STATIC_REF_PATTERN_KEY]

        text = re.sub(static_ref_re_pattern, _get_static_path, text)

        if settings and settings.get(USE_PELICAN_LIKE_REF_KEY, False):
            text = re.sub(
                PELICAN_LIKE_HREF_PATTERN,
                _parse_pelican_like_reference,
                text,
                flags=re.X,
            )

        return text
    elif isinstance(text, list):
        return [parse_static_references(instance, item) for item in text]
    else:
        return text


class StaticPath(object):
    def __init__(self, source, destination, url, extra):
        self._source = source
        self._original_destination = destination
        self._destination = destination
        self._original_url = url
        self._url = url
        self._extra = extra

    @property
    def source(self):
        return self._source

    @property
    def original_destination(self):
        return self._original_destination

    @property
    def destination(self):
        return self._destination

    @destination.setter
    def destination(self, value):
        self._destination = value

    @property
    def original_url(self):
        return self._original_url

    @property
    def url(self):
        return self._url

    @url.setter
    def url(self, value):
        self._url = value

    @property
    def extra(self):
        return self._extra


class AutoStaticGenerator(generators.Generator):
    """copy static paths (what you want to copy, like images, medias etc.
    to output"""

    autostatic_generator_init = signal("autostatic_generator_init")
    autostatic_generator_preread = signal("autostatic_generator_preread")
    autostatic_generator_context = signal("autostatic_generator_context")
    autostatic_generator_finalized = signal("autostatic_generator_finalized")

    def __init__(self, *args, **kwargs):
        super(AutoStaticGenerator, self).__init__(*args, **kwargs)
        self.autostatic_files = []
        self.autostatic_generator_init.send(self)

    def add_static_path(self, source_path, save_as):
        try:
            static = self.readers.read_file(
                base_path=self.path,
                path=source_path,
                content_class=Static,
                fmt="static",
                context=self.context,
                preread_signal=self.autostatic_generator_preread,
                preread_sender=self,
                context_signal=self.autostatic_generator_context,
                context_sender=self,
            )
            static.override_save_as = save_as
            self.autostatic_files.append(static)
            self.add_source_path(static)
        except Exception as e:
            logger.error(
                "Could not process %s\n%s",
                source_path,
                e,
                exc_info=self.settings.get("DEBUG", False),
            )

    def finalize_context(self):
        for save_as, source_path in detected_autostatic_paths.items():
            self.add_static_path(source_path, save_as)

        self._update_context(("autostatic_files",))
        self.autostatic_generator_finalized.send(self)

    def generate_output(self, writer):
        # copy all Static files
        for sc in self.autostatic_files:
            source_path = os.path.join(self.path, sc.source_path)
            save_as = os.path.join(self.output_path, sc.save_as)
            mkdir_p(os.path.dirname(save_as))
            shutil.copy2(source_path, save_as)
            logger.info("Copying %s to %s", sc.source_path, sc.save_as)


def find_static_references(instance):
    if hasattr(instance, "_content"):
        instance._content = parse_static_references(instance, instance._content)
    if hasattr(instance, "_summary"):
        instance._summary = parse_static_references(instance, instance._summary)

    for key in instance.metadata.keys():
        instance.metadata[key] = parse_static_references(
            instance, instance.metadata[key]
        )
        try:
            setattr(
                instance,
                key.lower(),
                parse_static_references(instance, getattr(instance, key.lower())),
            )
        except AttributeError:
            pass


def get_generators(_):
    return AutoStaticGenerator


def autostatic_generator_initialized(generator):
    global autostatic_generator
    autostatic_generator = generator


def generators_finished(_):
    global autostatic_generator
    autostatic_generator.finalize_context()


def register():
    signals.content_object_init.connect(find_static_references)
    signals.get_generators.connect(get_generators)
    AutoStaticGenerator.autostatic_generator_init.connect(
        autostatic_generator_initialized
    )
    signals.get_writer.connect(generators_finished)
