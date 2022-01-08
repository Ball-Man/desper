import os.path as pt
import collections
import json
import importlib
import re
import gc
import heapq
from collections import OrderedDict
from dataclasses import dataclass, field
from typing import Any

import desper

RESOURCE_STRING_REGEX = re.compile(r'\$\{(.+)\}')
TYPE_STRING_REGEX = re.compile(r'\$type\{(.+)\}')
MODEL_STRING_REGEX = re.compile(r'\$model')
DEFAULT_WORLDS_LOCATION = 'worlds'
DEFAULT_WORLDS_EXTS = ('.json')


def get_resource_importer(location, accepted_exts):
    """Get an importer function for resources, based on filename.

    Given the resource subfolder and accepted extensions, return a
    function in the form of :py:attr:`GameModel.LAMBDA_SIG` that will
    only accept files in the given resource subfolder(`location`) and
    returns the path to the given media resource if it's considered
    accepted.

    :param location: The resource subfolder for the game where resource
                     should be stored(other directories won't be
                     accepted).
    :param accepted_exts: An iterable of extensions recognized as valid
                          resource file.
    """
    def importer(root, rel_path, model):
        """Return the joined path `root` + `rel_path` if accepted.

        :param root: The root resource directory.
        :param rel_path: The relative path from the resource directory
                         to the specific resource being analyzed.
        :return: The joined path `root` + `rel_path` if accepted, None
                 otherwise(as stated in :py:attr:`GameModel.LAMBDA_SIG`
                 ).
        """
        # Check for location
        location_splitted = location.split(pt.sep)
        rel_path_splitted: list = pt.dirname(rel_path).split(pt.sep)
        last_index = -1
        for loc in location_splitted:
            found = loc in rel_path_splitted
            found_index = rel_path_splitted.index(loc) if found else -1
            if (found and (last_index == -1 or found_index == last_index + 1)):
                last_index = found_index
            else:
                # Immediately drop if the location is inconsistent
                return None

        if pt.splitext(rel_path)[1] in accepted_exts:
            return pt.join(root, rel_path),

        return None

    return importer


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


class Handle:
    """A base class helper class for resource access.

    A Handle exposes a :py:meth:`get` method which loads a resource from
    given attributes(e.g. a filename) and caches it for later use.
    When deriving, the :py:meth:`__init__` and :py:meth:`_load` method
    should be overridden in order to reproduce the desired
    behaviour(correctly load and cache the desired resource).
    """
    _value = None

    def __del__(self):
        self.clear()

    def __getattr__(self, name):
        return getattr(self.get(), name)

    def _load(self):
        """Base method for resource loading.

        Implement this method to customize the loading process and make
        your own resource loading logic. This method should load the
        resource using any necessary attribute from `self`, and return
        it.
        """
        raise NotImplementedError

    def __call__(self):
        """Short for :meth:`get`."""
        return self.get()

    def get(self):
        """Get the handled resource(and cache it if it's not already).

        NB: This method generally doesn't need to be overridden.

        :return: The specific resource instance handled by this Handle.
        """
        if self._value is None:
            self._value = self._load()

        return self._value

    def clear(self):
        """Clear the cached resource.

        The cached value is wiped and will need to be reloaded(that is
        overhead) when calling :py:meth:`get`.
        This won't necessarily free the memory allocated by the given
        resource. The handle will simply "forget" about the value, which
        may or may not release the memory based on the garbage
        collector.
        """
        self._value = None

    @property
    def loaded(self):
        return self._value is not None


class IdentityHandle(Handle):
    """Special kind of :class:`Handle` that returns the given value.

    This handle accepts any value, and when :py:meth:`get` is called,
    returns the given value itself(basically, there is no "generated"
    value).

    This is used to inject manually resources into the resources
    dictionary of a :class:`GameModel`.
    """

    def __init__(self, value):
        super().__init__()
        self._value = value

    def _load(self):
        """Return the given value as it is."""
        return self._value


@dataclass(order=True)
class _PrioritizedDictEntry:
    """Class used to contain a prioritized entry for importer dicts.

    Used by :class:`ImporterDictBuilder` to keep track of the entries in
    a priority queue.
    """
    key_lambda: Any = field(compare=False)
    handle_type: Handle = field(compare=False)
    priority: int


class ImporterDictBuilder:
    """Builder class for importer dictionaries(for :class:`GameModel`)

    This class observes the GOF Builder pattern and facilitates the
    creation of importer dictionaries. In particular, it facilitates
    the creation of ordered dictionaries with a specified priority for
    each entity(since the order of the entries in the dictionary defines
    which resource is as first, this might be quite important for
    certain setups).

    Smaller values in priority will be placed first.

    A default instance of this class is constructed by default at module
    level attribute :py:attr:`importer_dict_builder` (so that, if not
    strictly necessary, you don't have to instantiate this class
    manually each time).
    """

    def __init__(self):
        self._queue = []

    def add_rule(self, key_lambda, handle_type, priority=0):
        """Add a resource importer rule, given the key and the handle.

        The `key_lambda` is a callable(usually a function). The
        `handle_type` is a subtype of :class:`Handle`. The `priority`
        helps defining the order in which the rules will be executed by
        the :class:`GameModel`.

        For more info about the meaning of `key_lambda` and
        `handle_type` see :class:`GameModel`.

        :param key_lambda: The lambda function used as a key inside the
                           importer dictionary.
        :param handle_type: A subtype of :class:`Handle` used as value
                            inside the importer dictionary for the given
                            lambda key.
        :param priority: An integer defining the order of execution for
                         rules inside the importer dict(lower values of
                         `priority` are placed first).
        :return: The :class:`ImporterDictBuilder` class instance(self),
                 so that multiple :py:meth:`add_rule` can be
                 concatenated.
        """
        heapq.heappush(self._queue, _PrioritizedDictEntry(
            key_lambda, handle_type, priority))
        return self

    def build(self):
        """Build and return an importer dictionary.

        Note that once an dictionary is built, the builder will be
        cleaned up(so it's not possible to build multiple times the same
        dictionary calling build multiple times).

        :return: An importer dictionary which rules are defined by
                 previous calls to :py:meth:`add_rule`.
        """
        importer_dict = OrderedDict()
        while self._queue:
            el = heapq.heappop(self._queue)
            importer_dict[el.key_lambda] = el.handle_type

        return importer_dict


importer_dict_builder = ImporterDictBuilder()
"""Pre-constructed instance of :class:`ImporterDictBuilder`."""


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


class ModuleResourceResolver:
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

    Attributes matching the regex defined in
    :py:attr:`TYPE_STRING_REGEX` will be translated into respective
    class types using :class:`ModuleResourceResolver`.

    Attributes matching the regex defined in
    :py:attr:`MODEL_STRING_REGEX` will be translated into the current
    :class:`GameModel` instance.

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

        # Match for class types
        match = TYPE_STRING_REGEX.fullmatch(x)
        if match is not None:
            return ModuleResourceResolver()(match.group(1))

        # Match for model
        match = MODEL_STRING_REGEX.fullmatch(x)
        if match is not None:
            return model

        # Match for model resources
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


class WorldHandle(Handle):
    """Handle implementation for a `desper.World`.

    This handle accepts a file(name). Components are specified by
    name (package.submodule...Class), and the handle will try to import
    the necessary packages/modules and finally retrieve the wanted
    class.

    A similar approach is used in order to import
    :class:`esper.Processor`s.
    """
    type_resolvers = ResolverStack((ModuleResourceResolver(),))
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
        cur_entity = 0
        for instance in sorted(
                data.get('instances', []), key=lambda inst: inst['id']):

            # Create all the empty entities needed
            while cur_entity < instance['id'] - 1:
                cur_entity = w.create_entity()

            # Retrieve all the components for the entity
            components = []
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
                        components.append(c)
                else:
                    components.append(comp_inst)

            # Add all the components in one call
            # This helps when using an AbstractWorld, where on_attach
            # is triggered after adding all the components, preventing
            # initialization order issues.
            w.create_entity(*components)
            cur_entity += 1

        return w

    def clear(self):
        if self._value is not None:
            self._value.clear_database()
            gc.collect()

        super().clear()
