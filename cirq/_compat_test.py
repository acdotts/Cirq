# Copyright 2019 The Cirq Developers
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import types

import numpy as np
import pandas as pd
import pytest
import sympy

import cirq.testing
from cirq._compat import (
    proper_repr,
    deprecated,
    deprecated_parameter,
    proper_eq,
    deprecate_attributes,
    deprecated_class,
)


def test_proper_repr():
    v = sympy.Symbol('t') * 3
    v2 = eval(proper_repr(v))
    assert v2 == v

    v = np.array([1, 2, 3], dtype=np.complex64)
    v2 = eval(proper_repr(v))
    np.testing.assert_array_equal(v2, v)
    assert v2.dtype == v.dtype


def test_proper_repr_data_frame():
    df = pd.DataFrame(
        index=[1, 2, 3], data=[[11, 21.0], [12, 22.0], [13, 23.0]], columns=['a', 'b']
    )
    df2 = eval(proper_repr(df))
    assert df2['a'].dtype == np.int64
    assert df2['b'].dtype == np.float
    pd.testing.assert_frame_equal(df2, df)

    df = pd.DataFrame(
        index=pd.Index([1, 2, 3], name='test'),
        data=[[11, 21.0], [12, 22.0], [13, 23.0]],
        columns=['a', 'b'],
    )
    df2 = eval(proper_repr(df))
    pd.testing.assert_frame_equal(df2, df)

    df = pd.DataFrame(
        index=pd.MultiIndex.from_tuples([(1, 2), (2, 3), (3, 4)], names=['x', 'y']),
        data=[[11, 21.0], [12, 22.0], [13, 23.0]],
        columns=pd.Index(['a', 'b'], name='c'),
    )
    df2 = eval(proper_repr(df))
    pd.testing.assert_frame_equal(df2, df)


def test_proper_eq():
    assert proper_eq(1, 1)
    assert not proper_eq(1, 2)

    assert proper_eq(np.array([1, 2, 3]), np.array([1, 2, 3]))
    assert not proper_eq(np.array([1, 2, 3]), np.array([1, 2, 3, 4]))
    assert not proper_eq(np.array([1, 2, 3]), np.array([[1, 2, 3]]))
    assert not proper_eq(np.array([1, 2, 3]), np.array([1, 4, 3]))

    assert proper_eq(pd.Index([1, 2, 3]), pd.Index([1, 2, 3]))
    assert not proper_eq(pd.Index([1, 2, 3]), pd.Index([1, 2, 3, 4]))
    assert not proper_eq(pd.Index([1, 2, 3]), pd.Index([1, 4, 3]))


def test_deprecated_with_name():
    @deprecated(deadline='v1.2', fix='Roll some dice.', name='test_func')
    def f(a, b):
        return a + b

    with cirq.testing.assert_deprecated(
        '_compat_test.py:',
        'test_func was used',
        'will be removed in cirq v1.2',
        'Roll some dice.',
        deadline='v1.2',
    ):
        assert f(1, 2) == 3


def test_deprecated():
    def new_func(a, b):
        return a + b

    @deprecated(deadline='v1.2', fix='Roll some dice.')
    def old_func(*args, **kwargs):
        return new_func(*args, **kwargs)

    with cirq.testing.assert_deprecated(
        '_compat_test.py:',
        'old_func was used',
        'will be removed in cirq v1.2',
        'Roll some dice.',
        deadline='v1.2',
    ):
        assert old_func(1, 2) == 3

    with pytest.raises(ValueError, match="Cirq should not use deprecated functionality"):
        old_func(1, 2)

    with pytest.raises(AssertionError, match="deadline should match vX.Y"):
        # pylint: disable=unused-variable
        # coverage: ignore
        @deprecated(deadline='invalid', fix='Roll some dice.')
        def badly_deprecated_func(*args, **kwargs):
            return new_func(*args, **kwargs)

        # pylint: enable=unused-variable


def test_deprecated_parameter():
    @deprecated_parameter(
        deadline='v1.2',
        fix='Double it yourself.',
        func_name='test_func',
        parameter_desc='double_count',
        match=lambda args, kwargs: 'double_count' in kwargs,
        rewrite=lambda args, kwargs: (args, {'new_count': kwargs['double_count'] * 2}),
    )
    def f(new_count):
        return new_count

    # Does not warn on usual use.
    with cirq.testing.assert_logs(count=0):
        assert f(1) == 1
        assert f(new_count=1) == 1

    with cirq.testing.assert_deprecated(
        '_compat_test.py:',
        'double_count parameter of test_func was used',
        'will be removed in cirq v1.2',
        'Double it yourself.',
        deadline='v1.2',
    ):
        # pylint: disable=unexpected-keyword-arg
        # pylint: disable=no-value-for-parameter
        assert f(double_count=1) == 2
        # pylint: enable=no-value-for-parameter
        # pylint: enable=unexpected-keyword-arg

    with pytest.raises(ValueError, match="Cirq should not use deprecated functionality"):
        # pylint: disable=unexpected-keyword-arg
        # pylint: disable=no-value-for-parameter
        f(double_count=1)
        # pylint: enable=no-value-for-parameter
        # pylint: enable=unexpected-keyword-arg

    with pytest.raises(AssertionError, match="deadline should match vX.Y"):

        @deprecated_parameter(
            deadline='invalid',
            fix='Double it yourself.',
            func_name='test_func',
            parameter_desc='double_count',
            match=lambda args, kwargs: 'double_count' in kwargs,
            rewrite=lambda args, kwargs: (args, {'new_count': kwargs['double_count'] * 2}),
        )
        # pylint: disable=unused-variable
        # coverage: ignore
        def f_with_badly_deprecated_param(new_count):
            return new_count

        # pylint: enable=unused-variable


def test_wrap_module():
    my_module = types.ModuleType('my_module', 'my doc string')
    my_module.foo = 'foo'
    my_module.bar = 'bar'
    assert 'foo' in my_module.__dict__
    assert 'bar' in my_module.__dict__
    assert 'zoo' not in my_module.__dict__

    with pytest.raises(AssertionError, match="deadline should match vX.Y"):
        deprecate_attributes(my_module, {'foo': ('invalid', 'use bar instead')})

    wrapped = deprecate_attributes(my_module, {'foo': ('v0.6', 'use bar instead')})
    # Dunder methods
    assert wrapped.__doc__ == 'my doc string'
    assert wrapped.__name__ == 'my_module'
    # Test dict is correct.
    assert 'foo' in wrapped.__dict__
    assert 'bar' in wrapped.__dict__
    assert 'zoo' not in wrapped.__dict__

    # Deprecation capability.
    with cirq.testing.assert_deprecated(
        '_compat_test.py:',
        'foo was used but is deprecated.',
        'will be removed in cirq v0.6',
        'use bar instead',
        deadline='v0.6',
    ):
        _ = wrapped.foo

    with pytest.raises(ValueError, match="Cirq should not use deprecated functionality"):
        _ = wrapped.foo

    with cirq.testing.assert_logs(count=0):
        _ = wrapped.bar


def test_deprecated_class():
    class NewClass:
        def __init__(self, a):
            self._a = a

        @property
        def a(self):
            return self._a

        def __repr__(self):
            return f"NewClass: {self.a}"

        @classmethod
        def hello(cls):
            return f"hello {cls}"

    @deprecated_class(deadline="v1.2", fix="theFix", name="foo")
    class OldClass(NewClass):
        """The OldClass docs"""

    assert OldClass.__doc__.startswith("THIS CLASS IS DEPRECATED")
    assert "OldClass docs" in OldClass.__doc__

    with cirq.testing.assert_deprecated(
        '_compat_test.py:',
        'foo was used but is deprecated',
        'will be removed in cirq v1.2',
        'theFix',
        deadline="v1.2",
    ):
        old_obj = OldClass("1")
        assert repr(old_obj) == "NewClass: 1"
        assert "OldClass" in old_obj.hello()

    with pytest.raises(ValueError, match="Cirq should not use deprecated functionality"):
        OldClass("1")

    with pytest.raises(AssertionError, match="deadline should match vX.Y"):
        # pylint: disable=unused-variable
        # coverage: ignore
        @deprecated_class(deadline="invalid", fix="theFix", name="foo")
        class BadlyDeprecatedClass(NewClass):
            ...

        # pylint: enable=unused-variable
