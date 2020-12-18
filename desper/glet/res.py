import os.path as pt
import json
import importlib
import collections
import re

import desper

import pyglet


DEFAULT_SPRITES_LOCATION = 'sprites'
DEFAULT_IMAGE_EXTS = ('.png', '.bmp', '.jpg', '.jpeg')

DEFAULT_ANIMATION_EXTS = ('.json')
"""Default exts for the animation metadata files."""
DEFAULT_ANIMATION_SHEET_EXTS = DEFAULT_IMAGE_EXTS
"""Default exts for the animation sprite sheet files."""

DEFAULT_MEDIA_LOCATION = 'media'
DEFAULT_MEDIA_EXTS = ('.wav', '.mp4', '.mp3', '.ogg')

DEFAULT_FONT_LOCATION = 'fonts'
DEFAULT_FONT_EXTS = ('.ttf', '.otf')

DEFAULT_WORLDS_LOCATION = 'worlds'
DEFAULT_WORLDS_EXTS = ('.json')
RESOURCE_STRING_REGEX = re.compile(r'\$\{(.+)\}')


def _pyglet_path(path):
    """Manipulate path to match pyglet.resource requirements.

    Note that pyglet.resource requires paths to be relative to the
    current dir and using only '/' as separator.
    Note also that changing pyglet.resource.path this behaviour can be
    changed, but in this case it should not.

    :param path: The target path(absolute or using '\\').
    :return: A path usable with pyglet.resource.
    """
    return pt.relpath(path, pt.curdir).replace(pt.sep, '/')


def resource_from_path(res, rel_path, default=None):
    """Get a specific resource :class:`Handle` from a res dictionary.

    The given path should be relative to one of the resource directories
    chosen when initializing the :class:`GameModel`.

    :param res: A resource dictionary (presumably from a
                :class:`GameModel`).
    :param rel_path: Relative path from one of the resources root
                     directory(chosen when initializing the
                     :class:`GameModel`).
    :param default: The default returned value if the queried
                    :class:`Handle` doesn't exist. Defaults to ``None``.
    :return: The :class:`Handle` loaded from the given `rel_path` if
             exists, `default` otherwise.
    """
    # Convert to posix path if needed
    rel_path = rel_path.replace(pt.sep, '/')

    # Remove extension if required
    if not desper.options['resource_extensions']:
        rel_path = pt.splitext(rel_path)[0]

    p = res
    for path in rel_path.split('/'):
        p = p.get(path, None)

        if p is None:
            return default

    return p


def get_image_importer():
    """Get an importer function for `pyglet.image.AbstractImage`.

    Given the resource subfolder and accepted extensions, return a
    function in the form of :py:attr:`GameModel.LAMBDA_SIG` that will
    only accept files in the given resource subfolder(`location`) and
    returns the path to the given image if it's considered accepted
    (designed to be used with :class:`ImageHandle`).

    :return: A function usable as key in an `importer_dict`.
    """
    return desper.get_resource_importer(location=DEFAULT_SPRITES_LOCATION,
                                        accepted_exts=DEFAULT_IMAGE_EXTS)


def get_animation_importer():
    """Get an importer function for `pyglet.image.animation.Animation`.

    Given the resource subfolder and accepted extensions, return a
    function in the form of :py:attr:`GameModel.LAMBDA_SIG` that will
    only accept files in the given resource subfolder(`location`) and
    returns the path to the given image if it's considered accepted
    (designed to be used with :class:`AnimationHandle`).

    For more information about the metadata file format see
    :class:`AnimationHandle`.

    :param location: The resource subfolder for the game where sprites
                     should be stored(other directories won't be
                     accepted).
    :param accepted_exts: An iterable of extensions recognized as valid
                          animation metadata.
    :param accepted_sheet_exts: An iterable of extensions recognized as
                                valid animation files(sprite sheets).
    :return: A function usable as key in an `importer_dict`.
    """
    return desper.get_resource_importer(location=DEFAULT_SPRITES_LOCATION,
                                        accepted_exts=DEFAULT_ANIMATION_EXTS)


def get_media_importer():
    """Get an importer function for `pyglet.media.Source` resources.

    Given the resource subfolder and accepted extensions, return a
    function in the form of :py:attr:`GameModel.LAMBDA_SIG` that will
    only accept files in the given resource subfolder(`location`) and
    returns the path to the given media resource if it's considered
    accepted.
    (Designed to be used with :class:`MediaHandle`).

    Currently there is not metadata file, the resource is imported as it
    is (by default streamed from the disk, a custom importer function/handle
    might be necessary if pre-decoded resources are needed).

    :param location: The resource subfolder for the game where media
                     should be stored(other directories won't be
                     accepted).
    :param accepted_exts: An iterable of extensions recognized as valid
                          media metadata.
    """
    return desper.get_resource_importer(location=DEFAULT_MEDIA_LOCATION,
                                        accepted_exts=DEFAULT_MEDIA_EXTS)


def get_font_importer():
    """Get an importer function for pyglet fonts.

    The returned importer is suitable as key in an importer dictionary
    (for :class:`GameModel` subclasses) and will load the given font to
    memory directly(not using :class:`Handle` s).
    In fact, this importer always **refuses** the given resource(
    returns ``None``) because it immediately loads it using
    ``pyglet.resource.add_font``. Since ``add_font`` returns no resource
    instance, but only loads the font family, there is no need for a
    :class:`Handle` to contain the font.
    """

    location = DEFAULT_FONT_LOCATION
    accepted_exts = DEFAULT_FONT_EXTS

    def font_importer(root, rel_path, model):
        """Import font file if accepted.

        param root: The root resource directory.
        :param rel_path: The relative path from the resource directory
                         to the specific resource being analyzed.
        :return: Always None.
        """
        if (location in pt.dirname(rel_path) and pt.splitext(rel_path)[1] in
                accepted_exts):
            pyglet.resource.add_font(_pyglet_path(pt.join(root, rel_path)))

        return None

    return font_importer


def get_world_importer():
    """Get an importer function for worlds(:class:`WorldHandle`).

    :return: A function usable as key in an `importer_dict`.
    """
    lambd = desper.get_resource_importer(DEFAULT_WORLDS_LOCATION,
                                         DEFAULT_WORLDS_EXTS)

    def decorated_lambda(root, rel_path, model):
        ret = lambd(root, rel_path, model)
        if ret is None:
            return None

        ret = list(ret)
        ret.append(model)

        return ret

    return decorated_lambda


class ImageHandle(desper.Handle):
    """Handle implementation for a `pyglet.image.AbstractImage`.

    This is used for static images only. See :class:`AnimationHandle`
    for animated images(`pyglet.image.animation.Animation`).
    """

    def __init__(self, filename):
        """Construct a new Handle based on the given `filename`.

        :param filename: The filename that will be used to load the
                         desired resource.
        """
        super().__init__()

        # Manipulate the path for pyglet(pyglet.resource requires
        # relative paths using only '/')
        self._filename = _pyglet_path(filename)

    def _load(self):
        """Implementation of the load logic for this Handle type."""
        return pyglet.resource.image(self._filename)


class AnimationHandle(desper.Handle):
    """Handle implementation for a `pyglet.image.Animation`.

    This is used for animations only. For static images
    (`pyglet.image.AbstractImage`) see :class:`ImageHandle`.

    This Handle accepts a file in its constructor, which should be in
    a specific format(the extension doesn't matter).
    The file content should be in json format, with this structure:
        TBD

    This structure can be easily achieved by using `Aseprite
    <https://www.aseprite.org/>`_'s spritesheet export(by checking the
    JSON Data checkbox).
    """

    def __init__(self, filename):
        """Construct a new Handle for an animation file.

        The animation file should be in json format. For the correct
        data structure see the doc of :class:`AnimationHandle`.
        """
        super().__init__()

        self._filename = filename

    def _load(self):
        """Implementation of the load logic for this Handle type."""
        with open(self._filename) as fin:
            data = json.load(fin)
            if isinstance(data['frames'], dict):
                data['frames'] = data['frames'].values()

        meta = data['meta']
        filedir = _pyglet_path(pt.join(pt.dirname(
            self._filename), meta['image']))
        image = pyglet.resource.image(filedir)      # Full image
        # Extract single frames
        frames = [pyglet.image.AnimationFrame(image.get_region(
            frame['frame']['x'], frame['frame']['y'],
            frame['frame']['w'], frame['frame']['h']),
            frame['duration'] / 1000) for frame in data['frames']]

        # Set the given anchor to all the frames
        origin = meta['origin']
        for anim_frame in frames:
            anim_frame.image.anchor_x = origin['x']
            anim_frame.image.anchor_y = origin['y']

        return pyglet.image.Animation(
            frames=frames)


class MediaHandle(desper.Handle):
    """Handle implementation for a `pyglet.media.Source`.

    This is used to load a media resource(in games, probably an audio
    track or sfx). For non-raw data types, FFmpeg should be installed
    (this is required by pyglet).
    """

    def __init__(self, filename, streamed=True):
        """Construct a new MediaHandle, encapsulating the given file.

        :param filename: The path to the desired file.
        :param streamed: Whether the resource should be streamed from
                          disk when needed or decoded into memory.
        """
        super().__init__()

        self._filename = _pyglet_path(filename)
        self._streamed = streamed

    def _load(self):
        """Implementation of the load function for media loading."""
        return pyglet.resource.media(self._filename, self._streamed)


class ResourceResolver:
    """Resolve a string name representing a unique class or function.

    Callable, call passing a string in the format
    "package.subpackage.etc.etc.Class". If found, Class is returned.
    """

    def __init__(self):
        self._cache = {}

    def __call__(self, string):
        # Pull from cache if possible
        if self._cache.get(string) is not None:
            return self._cache[string]

        strings = string.split('.')

        # Import the module
        module = None
        incomplete = True
        for i, _ in enumerate(strings):
            try:
                module = importlib.import_module('.'.join(strings[0:i + 1]))
            except ModuleNotFoundError:
                incomplete = False
                break

        if incomplete:
            raise ValueError('Given string resolves to a module, not to a '
                             'class or callable.')

        # From the module import the subcomponents (classes, etc)
        last_index = i
        comp = module
        for comp_str in strings[last_index:]:
            comp = getattr(comp, comp_str)

        if not callable(comp):
            raise ValueError('Given string does not resolve to a class or '
                             'callable')

        # Save in cache and return
        self._cache[string] = comp
        return comp


def component_initializer(comp_type, args, kwargs, instance, world, model):
    """Return an initialized component, given the type and arguments.

    This function is made to be used in
    :py:attr:`WorldHandle.component_initializers`.

    :param comp_type: The type of the component to be initialized.
    :param args: List of arguments passed to this component from the
                 json.
    :param kwargs: Dictionary of keyword aguments passed to this
                   component from the json.
    :param instance: A dictionary containing the properties assigned
                     to the instance of this component(by default, "id")
                     is defined to be the entity numerical id.
    :param world: Instance of :class:`esper.World` of which this
                  component will be part.
    :param model: Instance of :class:`desper.GameModel`.
    :return: An initialized component.
    """
    return comp_type(*args, **kwargs)


def processor_initializer(proc_type, args, kwargs, world, model):
    """Return an initialized processor, given the type and arguments.

    This function is made to be used in
    :py:attr:`WorldHandle.processor_initializers`.

    :param comp_type: The type of the component to be initialized.
    :param args: List of arguments passed to this processor from the
                 json.
    :param kwargs: Dictionary of keyword aguments passed to this
                   processor from the json.
    :param world: Instance of :class:`esper.World` of which this
                  processor will be part.
    :param model: Instance of :class:`desper.GameModel`.
    :return: An initialized component.
    """
    return proc_type(*args, **kwargs)


def resources_initializer(args, kwargs, model, **kwa):
    """Substitute resource strings with the actual resources.

    Resources matching the regex defined in
    :py:attr:`RESOURCE_STRING_REGEX` will be translated into the
    respective resources (from the model resources dictionary).

    e.g. A parameter in the form ${sprite/1.png} will be translated into
    the resource in model.res['sprite']['1.png'].

    This function is made to be used in
    :py:attr:`WorldHandle.component_initializers` and in
    :py:attr:`WorldHandle.processor_initializers`.

    :param args: List of arguments passed to this component from the
                 json.
    :param kwargs: Dictionary of keyword aguments passed to this
                   component from the json.
    :param model: Instance of :class:`desper.GameModel`.
    :return: None, control is passed to the following resolver
    """
    def args_map(x):
        if type(x) is not str:
            return x

        match = RESOURCE_STRING_REGEX.fullmatch(x)
        if match is None:
            return x

        handle = resource_from_path(model.res, match.group(1))
        if handle is None:
            raise IndexError(f"Couldn't find resource named {x}")

        return handle.get()

    args[:] = map(args_map, args)
    kwargs.update({k: args_map(v) for k, v in kwargs.items()})

    return None


class ResolverStack:
    """Stack of callables, used to parse specific data.

    When calling a ResolverStack(operator ``()``) all the arguments
    are passed to the internal callables(inside the stack).
    If one of the callables returns a valid value, the value is returned
    from the ResolverStack call operation. If an internal callable
    returns ``None``, the following one is called.
    Exceptions will halt the process (they're not captured in any way).

    If the final callable can't resolve the input, but raises no
    exception(returns ``None``), or the stack is empty, an
    ``IndexError`` is raised.
    """

    def __init__(self, iterable=tuple()):
        self._stack = collections.deque(iterable)

    def __call__(self, *args, **kwargs):
        for resolver in reversed(self._stack):
            print(resolver)
            result = resolver(*args, **kwargs)
            if result is not None:
                return result

        # If no exception is thrown and no type is resolved, throw
        raise IndexError("No resolver was found for the input: "
                         f"{args}, {kwargs}")

    def push(self, resolver):
        """Push a resolver on top of the stack.

        :param resolver: The callable to be added.
        :raises TypeError: If ``resolver`` is not callable.
        """
        if not callable(resolver):
            raise TypeError()

        self._stack.append(resolver)

    def pop(self):
        """Pop the last resolver from the head of the stack.

        :return: The popped item.
        """
        return self._stack.pop()

    def clear(self):
        """Empty the stack."""
        self._stack.clear()

    def __len__(self):
        return len(self._stack)


class WorldHandle(desper.Handle):
    """Handle implementation for a `desper.World`.

    This handle accepts a file(name). Components are specified by
    name (package.submodule...Class), and the handle will try to import
    the necessary packages/modules and finally retrieve the wanted
    class.

    A similar approach is used in order to import
    :class:`esper.Processor`s.
    """
    type_resolvers = ResolverStack((ResourceResolver(),))
    """Stack of type resolvers."""

    component_initializers = ResolverStack((component_initializer,
                                            resources_initializer))
    """Stack of component initializers."""

    processor_initializers = ResolverStack((processor_initializer,
                                            resources_initializer))
    """Stack of processor initializers."""

    def __init__(self, filename, model):
        super().__init__()
        self._filename = filename
        self._model = model

    def _load(self):
        """Implementation of the load function."""
        with open(self._filename) as fin:
            data = json.load(fin)

        world_counter = 0

        # Get world type
        w_string = data['options']['world_type']
        w_type = self.type_resolvers(w_string)
        w = w_type()

        # Generate processors
        for processor in data.get('processors', []):
            proc_type = self.type_resolvers(processor['type'])
            args = processor.get('args', [])
            kwargs = processor.get('kwargs', {})

            proc_inst = self.processor_initializers(
                proc_type=proc_type, args=args, kwargs=kwargs, world=w,
                model=self._model)
            w.add_processor(proc_inst)

        # Generate instances, while retrieving the correct types
        for instance in data.get('instances', []):
            while world_counter < instance['id']:
                world_counter += 1
                w.create_entity()

            for comp in instance['comps']:
                comp_type = self.type_resolvers(comp['type'])

                args = comp.get('args', [])
                kwargs = comp.get('kwargs', {})
                comp_inst = self.component_initializers(
                    comp_type=comp_type, args=args, kwargs=kwargs,
                    instance=instance, world=w, model=self._model)

                # Support prototypes too
                if isinstance(comp_inst, desper.Prototype):
                    for c in comp_inst:
                        w.add_component(instance['id'], c)
                else:
                    w.add_component(instance['id'], comp_inst)

        return w


def glet_comp_initializer(comp_type, args, kwargs, instance, world, model):
    """Manage arguments in the correct way for :mod:`pyglet` components.

    This function is made to be used as resolver in the stack
    :py:attr:`WorldHandle.component_initializers`.

    No actual component is returned. Instead, None is returned, but the
    kwargs are parsed so that ``batch`` and ``groups`` are correctly
    resolved by the default initializer.
    """
    if issubclass(comp_type, pyglet.sprite.Sprite):
        # Set batch for the sprite
        kwargs['batch'] = model.get_batch(world)

        # Retrieve order group if present
        if 'group' in kwargs:
            kwargs['group'] = model.get_order_group(kwargs['group'])

    return None


class GletWorldHandle(WorldHandle):
    """Custom WorldHandle setup to better load pyglet components."""
    component_initializers = ResolverStack((component_initializer,
                                            resources_initializer,
                                            glet_comp_initializer))
