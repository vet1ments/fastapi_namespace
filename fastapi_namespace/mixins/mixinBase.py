from fastapi_namespace.resource import Resource
from fastapi_namespace.utils import delete_none
from fastapi_namespace.typings import MethodType
from typing import Iterable
from abc import ABCMeta
from fastapi.params import Depends

class _Meta(type):
    def __new__(mcs, name, bases, namespace):
        global_dependencies: Iterable[Depends] = getattr(bases[0], 'global_dependencies', None)
        if global_dependencies is not None:
            _global_dependencies = namespace.get('global_dependencies', [])
            global_dependencies = [*global_dependencies, *_global_dependencies]

        get_dependencies: Iterable[Depends] = getattr(bases[0], 'get_dependencies', None)
        if get_dependencies is not None:
            _get_dependencies = namespace.get('get_dependencies', [])
            get_dependencies = [*get_dependencies, *_get_dependencies]

        post_dependencies: Iterable[Depends] = getattr(bases[0], 'post_dependencies', None)
        if post_dependencies is not None:
            _post_dependencies = namespace.get('post_dependencies', [])
            post_dependencies = [*post_dependencies, *_post_dependencies]

        put_dependencies: Iterable[Depends] = getattr(bases[0], 'put_dependencies', None)
        if put_dependencies is not None:
            _put_dependencies = namespace.get('put_dependencies', [])
            put_dependencies = [*put_dependencies, *_put_dependencies]

        delete_dependencies: Iterable[Depends] = getattr(bases[0], 'delete_dependencies', None)
        if delete_dependencies is not None:
            _delete_dependencies = namespace.get('delete_dependencies', [])
            delete_dependencies = [*delete_dependencies, *_delete_dependencies]

        options_dependencies: Iterable[Depends] = getattr(bases[0], 'options_dependencies', None)
        if options_dependencies is not None:
            _options_dependencies = namespace.get('options_dependencies', [])
            options_dependencies = [*options_dependencies, *_options_dependencies]

        head_dependencies: Iterable[Depends] = getattr(bases[0], 'head_dependencies', None)
        if head_dependencies is not None:
            _head_dependencies = namespace.get('head_dependencies', [])
            head_dependencies = [*head_dependencies, *_head_dependencies]

        patch_dependencies: Iterable[Depends] = getattr(bases[0], 'patch_dependencies', None)
        if patch_dependencies is not None:
            _patch_dependencies = namespace.get('patch_dependencies', [])
            patch_dependencies = [*patch_dependencies, *_patch_dependencies]

        trace_dependencies: Iterable[Depends] = getattr(bases[0], 'trace_dependencies', None)
        if trace_dependencies is not None:
            _trace_dependencies = namespace.get('trace_dependencies', [])
            trace_dependencies = [*trace_dependencies, *_trace_dependencies]

        namespace.update(delete_none({
            'global_dependencies': global_dependencies,
            'get_dependencies': get_dependencies,
            'post_dependencies': post_dependencies,
            'put_dependencies': put_dependencies,
            'delete_dependencies': delete_dependencies,
            'options_dependencies': options_dependencies,
            'head_dependencies': head_dependencies,
            'patch_dependencies': patch_dependencies,
            'trace_dependencies': trace_dependencies,
        }))
        return type.__new__(mcs, name, bases, namespace)

class __Meta(_Meta, ABCMeta):
    pass

class MixinBase(Resource, metaclass=__Meta):
    global_dependencies: Iterable[Depends]
    get_dependencies: Iterable[Depends]
    post_dependencies: Iterable[Depends]
    put_dependencies: Iterable[Depends]
    delete_dependencies: Iterable[Depends]
    options_dependencies: Iterable[Depends]
    head_dependencies: Iterable[Depends]
    patch_dependencies: Iterable[Depends]
    trace_dependencies: Iterable[Depends]

    def _add_depends(self, type_: MethodType, depends: Depends) -> None:
        assert isinstance(depends, Depends), "Depends must be a Depends"
        key = f'{type_}_dependencies'
        dependencies = getattr(self, key, [])
        dependencies.append(depends)
        setattr(self, key, dependencies)

    def add_global_depends(self, depends: Depends) -> None:
        return self._add_depends('global', depends)

    def add_get_depends(self, depends: Depends) -> None:
        return self._add_depends('get', depends)

    def add_post_depends(self, depends: Depends) -> None:
        return self._add_depends('post', depends)

    def add_put_depends(self, depends: Depends) -> None:
        return self._add_depends('put', depends)

    def add_delete_depends(self, depends: Depends) -> None:
        return self._add_depends('delete', depends)

    def add_options_depends(self, depends: Depends) -> None:
        return self._add_depends('options', depends)

    def add_head_depends(self, depends: Depends) -> None:
        return self._add_depends('head', depends)

    def add_patch_depends(self, depends: Depends) -> None:
        return self._add_depends('patch', depends)

    def add_trace_depends(self, depends: Depends) -> None:
        return self._add_depends('trace', depends)