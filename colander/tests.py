import unittest

def invalid_exc(func, *arg, **kw):
    from colander import Invalid
    try:
        func(*arg, **kw)
    except Invalid, e:
        return e
    else:
        raise AssertionError('Invalid not raised') # pragma: no cover

class TestInvalid(unittest.TestCase):
    def _makeOne(self, node, msg=None, pos=None):
        from colander import Invalid
        exc = Invalid(node, msg)
        exc.pos = pos
        return exc

    def test_ctor(self):
        exc = self._makeOne(None, 'msg')
        self.assertEqual(exc.node, None)
        self.assertEqual(exc.msg, 'msg')
        self.assertEqual(exc.children, [])

    def test_add(self):
        exc = self._makeOne(None, 'msg')
        other = Dummy()
        exc.add(other)
        self.assertEqual(other.parent, exc)
        self.assertEqual(exc.children, [other])

    def test__keyname_no_parent(self):
        node = DummySchemaNode(None, name='name')
        exc = self._makeOne(None, '')
        exc.node = node
        self.assertEqual(exc._keyname(), 'name')

    def test__keyname_positional_parent(self):
        from colander import Positional
        parent = Dummy()
        parent.node = DummySchemaNode(Positional())
        exc = self._makeOne(None, '')
        exc.parent = parent
        exc.pos = 2
        self.assertEqual(exc._keyname(), '2')

    def test__keyname_nonpositional_parent(self):
        parent = Dummy()
        parent.node = DummySchemaNode(None)
        exc = self._makeOne(None, 'me')
        exc.parent = parent
        exc.pos = 2
        exc.node = DummySchemaNode(None, name='name')
        self.assertEqual(exc._keyname(), 'name')

    def test_paths(self):
        exc1 = self._makeOne(None, 'exc1')
        exc2 = self._makeOne(None, 'exc2') 
        exc3 = self._makeOne(None, 'exc3')
        exc4 = self._makeOne(None, 'exc4')
        exc1.add(exc2)
        exc2.add(exc3)
        exc1.add(exc4)
        paths = list(exc1.paths())
        self.assertEqual(paths, [(exc1, exc2, exc3), (exc1, exc4)])

    def test_asdict(self):
        from colander import Positional
        node1 = DummySchemaNode(None, 'node1')
        node2 = DummySchemaNode(Positional(), 'node2')
        node3 = DummySchemaNode(Positional(), 'node3')
        node4 = DummySchemaNode(Positional(), 'node4')
        exc1 = self._makeOne(node1, 'exc1', pos=1)
        exc2 = self._makeOne(node2, 'exc2', pos=2) 
        exc3 = self._makeOne(node3, 'exc3', pos=3)
        exc4 = self._makeOne(node4, 'exc4', pos=4)
        exc1.add(exc2)
        exc2.add(exc3)
        exc1.add(exc4)
        d = exc1.asdict()
        self.assertEqual(d, {'node1.node2.3': 'exc1; exc2; exc3',
                             'node1.node4': 'exc1; exc4'})

    def test___str__(self):
        from colander import Positional
        node1 = DummySchemaNode(None, 'node1')
        node2 = DummySchemaNode(Positional(), 'node2')
        node3 = DummySchemaNode(Positional(), 'node3')
        node4 = DummySchemaNode(Positional(), 'node4')
        exc1 = self._makeOne(node1, 'exc1', pos=1)
        exc2 = self._makeOne(node2, 'exc2', pos=2) 
        exc3 = self._makeOne(node3, 'exc3', pos=3)
        exc4 = self._makeOne(node4, 'exc4', pos=4)
        exc1.add(exc2)
        exc2.add(exc3)
        exc1.add(exc4)
        result = str(exc1)
        self.assertEqual(
            result,
            "{'node1.node2.3': 'exc1; exc2; exc3', 'node1.node4': 'exc1; exc4'}"
            )

    def test___setitem__fails(self):
        node = DummySchemaNode(None)
        exc = self._makeOne(node, 'msg')
        self.assertRaises(KeyError, exc.__setitem__, 'notfound', 'msg')

    def test___setitem__succeeds(self):
        node = DummySchemaNode(None)
        child = DummySchemaNode(None)
        child.name = 'found'
        node.children = [child]
        exc = self._makeOne(node, 'msg')
        exc['found'] = 'msg2'
        self.assertEqual(len(exc.children), 1)
        childexc = exc.children[0]
        self.assertEqual(childexc.pos, 0)
        self.assertEqual(childexc.node.name, 'found')

class TestAll(unittest.TestCase):
    def _makeOne(self, validators):
        from colander import All
        return All(*validators)

    def test_success(self):
        validator1 = DummyValidator()
        validator2 = DummyValidator()
        validator = self._makeOne([validator1, validator2])
        self.assertEqual(validator(None, None), None)

    def test_failure(self):
        validator1 = DummyValidator('msg1')
        validator2 = DummyValidator('msg2')
        validator = self._makeOne([validator1, validator2])
        e = invalid_exc(validator, None, None)
        self.assertEqual(e.msg, ['msg1', 'msg2'])

class TestFunction(unittest.TestCase):
    def _makeOne(self, *arg, **kw):
        from colander import Function
        return Function(*arg, **kw)

    def test_success_function_returns_True(self):
        validator = self._makeOne(lambda x: True)
        self.assertEqual(validator(None, None), None)

    def test_fail_function_returns_empty_string(self):
        validator = self._makeOne(lambda x: '')
        e = invalid_exc(validator, None, None)
        self.assertEqual(e.msg, 'Invalid value')

    def test_fail_function_returns_False(self):
        validator = self._makeOne(lambda x: False)
        e = invalid_exc(validator, None, None)
        self.assertEqual(e.msg, 'Invalid value')

    def test_fail_function_returns_string(self):
        validator = self._makeOne(lambda x: 'fail')
        e = invalid_exc(validator, None, None)
        self.assertEqual(e.msg, 'fail')

    def test_propagation(self):
        validator = self._makeOne(lambda x: 'a' in x, 'msg')
        self.assertRaises(TypeError, validator, None, None)

class TestRange(unittest.TestCase):
    def _makeOne(self, min=None, max=None):
        from colander import Range
        return Range(min=min, max=max)

    def test_success_no_bounds(self):
        validator = self._makeOne()
        self.assertEqual(validator(None, 1), None)

    def test_success_upper_bound_only(self):
        validator = self._makeOne(max=1)
        self.assertEqual(validator(None, -1), None)

    def test_success_minimum_bound_only(self):
        validator = self._makeOne(min=0)
        self.assertEqual(validator(None, 1), None)

    def test_success_min_and_max(self):
        validator = self._makeOne(min=1, max=1)
        self.assertEqual(validator(None, 1), None)

    def test_min_failure(self):
        validator = self._makeOne(min=1)
        e = invalid_exc(validator, None, 0)
        self.assertEqual(e.msg, '0 is less than minimum value 1')

    def test_max_failure(self):
        validator = self._makeOne(max=1)
        e = invalid_exc(validator, None, 2)
        self.assertEqual(e.msg, '2 is greater than maximum value 1')

class TestLength(unittest.TestCase):
    def _makeOne(self, min=None, max=None):
        from colander import Length
        return Length(min=min, max=max)

    def test_success_no_bounds(self):
        validator = self._makeOne()
        self.assertEqual(validator(None, ''), None)

    def test_success_upper_bound_only(self):
        validator = self._makeOne(max=1)
        self.assertEqual(validator(None, 'a'), None)

    def test_success_minimum_bound_only(self):
        validator = self._makeOne(min=0)
        self.assertEqual(validator(None, ''), None)

    def test_success_min_and_max(self):
        validator = self._makeOne(min=1, max=1)
        self.assertEqual(validator(None, 'a'), None)

    def test_min_failure(self):
        validator = self._makeOne(min=1)
        e = invalid_exc(validator, None, '')
        self.assertEqual(e.msg, 'Shorter than minimum length 1')

    def test_max_failure(self):
        validator = self._makeOne(max=1)
        e = invalid_exc(validator, None, 'ab')
        self.assertEqual(e.msg, 'Longer than maximum length 1')

class TestOneOf(unittest.TestCase):
    def _makeOne(self, values):
        from colander import OneOf
        return OneOf(values)

    def test_success(self):
        validator = self._makeOne([1])
        self.assertEqual(validator(None, 1), None)

    def test_failure(self):
        validator = self._makeOne([1, 2])
        e = invalid_exc(validator, None, None)
        self.assertEqual(e.msg, '"None" is not one of 1, 2')

class TestMapping(unittest.TestCase):
    def _makeOne(self, *arg, **kw):
        from colander import Mapping
        return Mapping(*arg, **kw)

    def test_ctor_bad_unknown(self):
        self.assertRaises(ValueError, self._makeOne, 'badarg')

    def test_ctor_good_unknown(self):
        try:
            self._makeOne('ignore')
            self._makeOne('raise')
            self._makeOne('preserve')
        except ValueError, e: # pragma: no cover
            raise AssertionError(e)

    def test_deserialize_not_a_mapping(self):
        node = DummySchemaNode(None)
        typ = self._makeOne()
        e = invalid_exc(typ.deserialize, node, None)
        self.failUnless(
            e.msg.startswith('None is not a mapping type'))

    def test_deserialize_no_subnodes(self):
        node = DummySchemaNode(None)
        typ = self._makeOne()
        result = typ.deserialize(node, {})
        self.assertEqual(result, {})

    def test_deserialize_ok(self):
        node = DummySchemaNode(None)
        node.children = [DummySchemaNode(None, name='a')]
        typ = self._makeOne()
        result = typ.deserialize(node, {'a':1})
        self.assertEqual(result, {'a':1})

    def test_deserialize_unknown_raise(self):
        node = DummySchemaNode(None)
        node.children = [DummySchemaNode(None, name='a')]
        typ = self._makeOne(unknown='raise')
        e = invalid_exc(typ.deserialize, node, {'a':1, 'b':2})
        self.assertEqual(e.msg, "Unrecognized keys in mapping: {'b': 2}")

    def test_deserialize_unknown_preserve(self):
        node = DummySchemaNode(None)
        node.children = [DummySchemaNode(None, name='a')]
        typ = self._makeOne(unknown='preserve')
        result = typ.deserialize(node, {'a':1, 'b':2})
        self.assertEqual(result, {'a':1, 'b':2})

    def test_deserialize_subnodes_raise(self):
        node = DummySchemaNode(None)
        node.children = [
            DummySchemaNode(None, name='a', exc='Wrong 2'),
            DummySchemaNode(None, name='b', exc='Wrong 2'),
            ]
        typ = self._makeOne()
        e = invalid_exc(typ.deserialize, node, {'a':1, 'b':2})
        self.assertEqual(e.msg, None)
        self.assertEqual(len(e.children), 2)

    def test_deserialize_subnode_missing_default(self):
        node = DummySchemaNode(None)
        node.children = [
            DummySchemaNode(None, name='a'),
            DummySchemaNode(None, name='b', default='abc'),
            ]
        typ = self._makeOne()
        result = typ.deserialize(node, {'a':1})
        self.assertEqual(result, {'a':1, 'b':'abc'})

    def test_deserialize_subnode_missing_nodefault(self):
        node = DummySchemaNode(None)
        node.children = [
            DummySchemaNode(None, name='a'),
            DummySchemaNode(None, name='b'),
            ]
        typ = self._makeOne()
        e = invalid_exc(typ.deserialize, node, {'a':1})
        self.assertEqual(e.children[0].msg, '"b" is required but missing')

    def test_deserialize_subnode_partial(self):
        node = DummySchemaNode(None)
        node.children = [
            DummySchemaNode(None, name='a'),
            DummySchemaNode(None, name='b'),
            ]
        typ = self._makeOne(partial=True)
        result = typ.deserialize(node, {'a':1})
        self.assertEqual(result, {'a':1})

    def test_serialize_not_a_mapping(self):
        node = DummySchemaNode(None)
        typ = self._makeOne()
        e = invalid_exc(typ.serialize, node, None)
        self.failUnless(
            e.msg.startswith('None is not a mapping type'))

    def test_serialize_no_subnodes(self):
        node = DummySchemaNode(None)
        typ = self._makeOne()
        result = typ.serialize(node, {})
        self.assertEqual(result, {})

    def test_serialize_ok(self):
        node = DummySchemaNode(None)
        node.children = [DummySchemaNode(None, name='a')]
        typ = self._makeOne()
        result = typ.serialize(node, {'a':1})
        self.assertEqual(result, {'a':1})

    def test_serialize_subnode_partial(self):
        node = DummySchemaNode(None)
        node.children = [
            DummySchemaNode(None, name='a'),
            DummySchemaNode(None, name='b'),
            ]
        typ = self._makeOne()
        result = typ.serialize(node, {'a':1})
        self.assertEqual(result, {'a':1})

    def test_serialize_partial_with_default(self):
        node = DummySchemaNode(None)
        node.children = [
            DummySchemaNode(None, name='a'),
            DummySchemaNode(None, name='b', default='abc'),
            ]
        typ = self._makeOne()
        result = typ.serialize(node, {'a':1})
        self.assertEqual(result, {'a':1, 'b':'abc'})

    def test_serialize_with_unknown(self):
        node = DummySchemaNode(None)
        node.children = [
            DummySchemaNode(None, name='a'),
            ]
        typ = self._makeOne()
        result = typ.serialize(node, {'a':1, 'b':2})
        self.assertEqual(result, {'a':1})

class TestTuple(unittest.TestCase):
    def _makeOne(self):
        from colander import Tuple
        return Tuple()

    def test_deserialize_not_iterable(self):
        node = DummySchemaNode(None)
        typ = self._makeOne()
        e = invalid_exc(typ.deserialize, node, None)
        self.assertEqual(
            e.msg,
            'None is not iterable')
        self.assertEqual(e.node, node)

    def test_deserialize_no_subnodes(self):
        node = DummySchemaNode(None)
        typ = self._makeOne()
        result = typ.deserialize(node, ())
        self.assertEqual(result, ())

    def test_deserialize_ok(self):
        node = DummySchemaNode(None)
        node.children = [DummySchemaNode(None, name='a')]
        typ = self._makeOne()
        result = typ.deserialize(node, ('a',))
        self.assertEqual(result, ('a',))

    def test_deserialize_toobig(self):
        node = DummySchemaNode(None)
        node.children = [DummySchemaNode(None, name='a')]
        typ = self._makeOne()
        e = invalid_exc(typ.deserialize, node, ('a','b'))
        self.assertEqual(e.msg,
           "('a', 'b') has an incorrect number of elements (expected 1, was 2)")

    def test_deserialize_toosmall(self):
        node = DummySchemaNode(None)
        node.children = [DummySchemaNode(None, name='a')]
        typ = self._makeOne()
        e = invalid_exc(typ.deserialize, node, ())
        self.assertEqual(e.msg,
           "() has an incorrect number of elements (expected 1, was 0)")

    def test_deserialize_subnodes_raise(self):
        node = DummySchemaNode(None)
        node.children = [
            DummySchemaNode(None, name='a', exc='Wrong 2'),
            DummySchemaNode(None, name='b', exc='Wrong 2'),
            ]
        typ = self._makeOne()
        e = invalid_exc(typ.deserialize, node, ('1', '2'))
        self.assertEqual(e.msg, None)
        self.assertEqual(len(e.children), 2)

    def test_serialize_not_iterable(self):
        node = DummySchemaNode(None)
        typ = self._makeOne()
        e = invalid_exc(typ.serialize, node, None)
        self.assertEqual(
            e.msg,
            'None is not iterable')
        self.assertEqual(e.node, node)

    def test_serialize_no_subnodes(self):
        node = DummySchemaNode(None)
        typ = self._makeOne()
        result = typ.serialize(node, ())
        self.assertEqual(result, ())

    def test_serialize_ok(self):
        node = DummySchemaNode(None)
        node.children = [DummySchemaNode(None, name='a')]
        typ = self._makeOne()
        result = typ.serialize(node, ('a',))
        self.assertEqual(result, ('a',))

    def test_serialize_toobig(self):
        node = DummySchemaNode(None)
        node.children = [DummySchemaNode(None, name='a')]
        typ = self._makeOne()
        e = invalid_exc(typ.serialize, node, ('a','b'))
        self.assertEqual(e.msg,
           "('a', 'b') has an incorrect number of elements (expected 1, was 2)")

    def test_serialize_toosmall(self):
        node = DummySchemaNode(None)
        node.children = [DummySchemaNode(None, name='a')]
        typ = self._makeOne()
        e = invalid_exc(typ.serialize, node, ())
        self.assertEqual(e.msg,
           "() has an incorrect number of elements (expected 1, was 0)")

    def test_serialize_subnodes_raise(self):
        node = DummySchemaNode(None)
        node.children = [
            DummySchemaNode(None, name='a', exc='Wrong 2'),
            DummySchemaNode(None, name='b', exc='Wrong 2'),
            ]
        typ = self._makeOne()
        e = invalid_exc(typ.serialize, node, ('1', '2'))
        self.assertEqual(e.msg, None)
        self.assertEqual(len(e.children), 2)

class TestSequence(unittest.TestCase):
    def _makeOne(self, **kw):
        from colander import Sequence
        return Sequence(**kw)

    def test_alias(self):
        from colander import Seq
        from colander import Sequence
        self.assertEqual(Seq, Sequence)

    def test_deserialize_not_iterable(self):
        node = DummySchemaNode(None)
        typ = self._makeOne()
        node.children = [node]
        e = invalid_exc(typ.deserialize, node, None)
        self.assertEqual(
            e.msg,
            'None is not iterable')
        self.assertEqual(e.node, node)

    def test_deserialize_not_iterable_accept_scalar(self):
        node = DummySchemaNode(None)
        typ = self._makeOne(accept_scalar=True)
        node.children = [node]
        result = typ.deserialize(node, None)
        self.assertEqual(result, [None])

    def test_deserialize_no_subnodes(self):
        typ = self._makeOne()
        node = DummySchemaNode(None)
        node.children = [node]
        result = typ.deserialize(node, ())
        self.assertEqual(result, [])

    def test_deserialize_ok(self):
        node = DummySchemaNode(None)
        node.children = [DummySchemaNode(None, name='a')]
        typ = self._makeOne()
        node.children = [node]
        result = typ.deserialize(node, ('a',))
        self.assertEqual(result, ['a'])

    def test_deserialize_subnodes_raise(self):
        node = DummySchemaNode(None, exc='Wrong')
        typ = self._makeOne()
        node.children = [node]
        e = invalid_exc(typ.deserialize, node, ('1', '2'))
        self.assertEqual(e.msg, None)
        self.assertEqual(len(e.children), 2)

    def test_serialize_not_iterable(self):
        node = DummySchemaNode(None)
        typ = self._makeOne()
        node.children = [node]
        e = invalid_exc(typ.serialize, node, None)
        self.assertEqual(
            e.msg,
            'None is not iterable')
        self.assertEqual(e.node, node)

    def test_serialize_not_iterable_accept_scalar(self):
        node = DummySchemaNode(None)
        typ = self._makeOne(accept_scalar=True)
        node.children = [node]
        result = typ.serialize(node, None)
        self.assertEqual(result, [None])

    def test_serialize_no_subnodes(self):
        node = DummySchemaNode(None)
        node.children = [node]
        typ = self._makeOne()
        result = typ.serialize(node, ())
        self.assertEqual(result, [])

    def test_serialize_ok(self):
        node = DummySchemaNode(None)
        node.children = [DummySchemaNode(None, name='a')]
        typ = self._makeOne()
        result = typ.serialize(node, ('a',))
        self.assertEqual(result, ['a'])

    def test_serialize_subnodes_raise(self):
        node = DummySchemaNode(None, exc='Wrong')
        typ = self._makeOne()
        node.children = [node]
        e = invalid_exc(typ.serialize, node, ('1', '2'))
        self.assertEqual(e.msg, None)
        self.assertEqual(len(e.children), 2)

class TestString(unittest.TestCase):
    def _makeOne(self, encoding='utf-8'):
        from colander import String
        return String(encoding)

    def test_alias(self):
        from colander import Str
        from colander import String
        self.assertEqual(Str, String)

    def test_serialize_emptystring_required(self):
        val = ''
        node = DummySchemaNode(None)
        typ = self._makeOne()
        e = invalid_exc(typ.deserialize, node, val)
        self.assertEqual(e.msg, 'Required')

    def test_serialize_emptystring_notrequired(self):
        val = ''
        node = DummySchemaNode(None, default='default')
        typ = self._makeOne()
        result = typ.deserialize(node, val)
        self.assertEqual(result, 'default')

    def test_deserialize_uncooperative(self):
        val = Uncooperative()
        node = DummySchemaNode(None)
        typ = self._makeOne()
        e = invalid_exc(typ.deserialize, node, val)
        self.failUnless(e.msg)

    def test_deserialize_unicode(self):
        uni = u'\xf8'
        node = DummySchemaNode(None)
        typ = self._makeOne()
        result = typ.deserialize(node, uni)
        self.assertEqual(result, uni)

    def test_deserialize_from_utf8(self):
        utf8 = '\xc3\xb8'
        uni = u'\xf8'
        node = DummySchemaNode(None)
        typ = self._makeOne()
        result = typ.deserialize(node, utf8)
        self.assertEqual(result, uni)

    def test_deserialize_from_utf16(self):
        utf16 = '\xff\xfe\xf8\x00'
        uni = u'\xf8'
        node = DummySchemaNode(None)
        typ = self._makeOne('utf-16')
        result = typ.deserialize(node, utf16)
        self.assertEqual(result, uni)

    def test_serialize_uncooperative(self):
        val = Uncooperative()
        node = DummySchemaNode(None)
        typ = self._makeOne()
        e = invalid_exc(typ.serialize, node, val)
        self.failUnless(e.msg)

    def test_serialize_to_utf8(self):
        utf8 = '\xc3\xb8'
        uni = u'\xf8'
        node = DummySchemaNode(None)
        typ = self._makeOne()
        result = typ.serialize(node, uni)
        self.assertEqual(result, utf8)

    def test_serialize_to_utf16(self):
        utf16 = '\xff\xfe\xf8\x00'
        uni = u'\xf8'
        node = DummySchemaNode(None)
        typ = self._makeOne('utf-16')
        result = typ.serialize(node, uni)
        self.assertEqual(result, utf16)

    def test_serialize_string_with_high_unresolveable_high_order_chars(self):
        not_utf8 = '\xff\xfe\xf8\x00'
        node = DummySchemaNode(None)
        typ = self._makeOne('utf-8')
        e = invalid_exc(typ.serialize, node, not_utf8)
        self.failUnless('cannot be serialized to str' in e.msg)
        

class TestInteger(unittest.TestCase):
    def _makeOne(self):
        from colander import Integer
        return Integer()

    def test_alias(self):
        from colander import Int
        from colander import Integer
        self.assertEqual(Int, Integer)

    def test_serialize_emptystring_required(self):
        val = ''
        node = DummySchemaNode(None)
        typ = self._makeOne()
        e = invalid_exc(typ.deserialize, node, val)
        self.assertEqual(e.msg, 'Required')

    def test_serialize_emptystring_notrequired(self):
        val = ''
        node = DummySchemaNode(None, default='default')
        typ = self._makeOne()
        result = typ.deserialize(node, val)
        self.assertEqual(result, 'default')

    def test_deserialize_fails(self):
        val = 'P'
        node = DummySchemaNode(None)
        typ = self._makeOne()
        e = invalid_exc(typ.deserialize, node, val)
        self.failUnless(e.msg)

    def test_deserialize_ok(self):
        val = '1'
        node = DummySchemaNode(None)
        typ = self._makeOne()
        result = typ.deserialize(node, val)
        self.assertEqual(result, 1)

    def test_serialize_fails(self):
        val = 'P'
        node = DummySchemaNode(None)
        typ = self._makeOne()
        e = invalid_exc(typ.serialize, node, val)
        self.failUnless(e.msg)

    def test_serialize_ok(self):
        val = 1
        node = DummySchemaNode(None)
        typ = self._makeOne()
        result = typ.serialize(node, val)
        self.assertEqual(result, '1')

class TestFloat(unittest.TestCase):
    def _makeOne(self):
        from colander import Float
        return Float()

    def test_serialize_emptystring_required(self):
        val = ''
        node = DummySchemaNode(None)
        typ = self._makeOne()
        e = invalid_exc(typ.deserialize, node, val)
        self.assertEqual(e.msg, 'Required')

    def test_serialize_emptystring_notrequired(self):
        val = ''
        node = DummySchemaNode(None, default='default')
        typ = self._makeOne()
        result = typ.deserialize(node, val)
        self.assertEqual(result, 'default')

    def test_deserialize_fails(self):
        val = 'P'
        node = DummySchemaNode(None)
        typ = self._makeOne()
        e = invalid_exc(typ.deserialize, node, val)
        self.failUnless(e.msg)

    def test_deserialize_ok(self):
        val = '1.0'
        node = DummySchemaNode(None)
        typ = self._makeOne()
        result = typ.deserialize(node, val)
        self.assertEqual(result, 1.0)

    def test_serialize_fails(self):
        val = 'P'
        node = DummySchemaNode(None)
        typ = self._makeOne()
        e = invalid_exc(typ.serialize, node, val)
        self.failUnless(e.msg)

    def test_serialize_ok(self):
        val = 1.0
        node = DummySchemaNode(None)
        typ = self._makeOne()
        result = typ.serialize(node, val)
        self.assertEqual(result, '1.0')

class TestBoolean(unittest.TestCase):
    def _makeOne(self):
        from colander import Boolean
        return Boolean()

    def test_alias(self):
        from colander import Bool
        from colander import Boolean
        self.assertEqual(Bool, Boolean)

    def test_serialize_emptystring_required(self):
        val = ''
        node = DummySchemaNode(None)
        typ = self._makeOne()
        e = invalid_exc(typ.deserialize, node, val)
        self.assertEqual(e.msg, 'Required')

    def test_serialize_emptystring_notrequired(self):
        val = ''
        node = DummySchemaNode(None, default='default')
        typ = self._makeOne()
        result = typ.deserialize(node, val)
        self.assertEqual(result, True)

    def test_deserialize(self):
        typ = self._makeOne()
        node = DummySchemaNode(None)
        self.assertEqual(typ.deserialize(node, 'false'), False)
        self.assertEqual(typ.deserialize(node, 'FALSE'), False)
        self.assertEqual(typ.deserialize(node, '0'), False)
        self.assertEqual(typ.deserialize(node, 'true'), True)
        self.assertEqual(typ.deserialize(node, 'other'), True)

    def test_deserialize_unstringable(self):
        typ = self._makeOne()
        node = DummySchemaNode(None)
        e = invalid_exc(typ.deserialize, node, Uncooperative())
        self.failUnless(e.msg.endswith('not a string'))

    def test_serialize(self):
        typ = self._makeOne()
        node = DummySchemaNode(None)
        self.assertEqual(typ.serialize(node, 1), 'true')
        self.assertEqual(typ.serialize(node, True), 'true')
        self.assertEqual(typ.serialize(node, None), 'false')
        self.assertEqual(typ.serialize(node, False), 'false')

class TestGlobalObject(unittest.TestCase):
    def _makeOne(self, package=None):
        from colander import GlobalObject
        return GlobalObject(package)

    def test_zope_dottedname_style_resolve_absolute(self):
        typ = self._makeOne()
        result = typ._zope_dottedname_style(None,
            'colander.tests.TestGlobalObject')
        self.assertEqual(result, self.__class__)
        
    def test_zope_dottedname_style_irrresolveable_absolute(self):
        typ = self._makeOne()
        self.assertRaises(ImportError, typ._zope_dottedname_style, None,
            'colander.tests.nonexisting')

    def test__zope_dottedname_style_resolve_relative(self):
        import colander
        typ = self._makeOne(package=colander)
        result = typ._zope_dottedname_style(None, '.tests.TestGlobalObject')
        self.assertEqual(result, self.__class__)

    def test__zope_dottedname_style_resolve_relative_leading_dots(self):
        import colander
        typ = self._makeOne(package=colander.tests)
        result = typ._zope_dottedname_style(None, '..tests.TestGlobalObject')
        self.assertEqual(result, self.__class__)

    def test__zope_dottedname_style_resolve_relative_is_dot(self):
        import colander.tests
        typ = self._makeOne(package=colander.tests)
        result = typ._zope_dottedname_style(None, '.')
        self.assertEqual(result, colander.tests)

    def test__zope_dottedname_style_irresolveable_relative_is_dot(self):
        typ = self._makeOne()
        e = invalid_exc(typ._zope_dottedname_style, None, '.')
        self.assertEqual(
            e.msg,
            'relative name "." irresolveable without package')

    def test_zope_dottedname_style_resolve_relative_nocurrentpackage(self):
        typ = self._makeOne()
        e = invalid_exc(typ._zope_dottedname_style, None, '.whatever')
        self.assertEqual(
            e.msg, 'relative name ".whatever" irresolveable without package')

    def test_zope_dottedname_style_irrresolveable_relative(self):
        import colander.tests
        typ = self._makeOne(package=colander)
        self.assertRaises(ImportError, typ._zope_dottedname_style, None,
                          '.notexisting')

    def test__zope_dottedname_style_resolveable_relative(self):
        import colander
        typ = self._makeOne(package=colander)
        result = typ._zope_dottedname_style(None, '.tests')
        from colander import tests
        self.assertEqual(result, tests)

    def test__zope_dottedname_style_irresolveable_absolute(self):
        typ = self._makeOne()
        self.assertRaises(ImportError,
                          typ._zope_dottedname_style, None, 'colander.fudge.bar')

    def test__zope_dottedname_style_resolveable_absolute(self):
        typ = self._makeOne()
        result = typ._zope_dottedname_style(None,
                                            'colander.tests.TestGlobalObject')
        self.assertEqual(result, self.__class__)

    def test__pkg_resources_style_resolve_absolute(self):
        typ = self._makeOne()
        result = typ._pkg_resources_style(None,
            'colander.tests:TestGlobalObject')
        self.assertEqual(result, self.__class__)
        
    def test__pkg_resources_style_irrresolveable_absolute(self):
        typ = self._makeOne()
        self.assertRaises(ImportError, typ._pkg_resources_style, None,
            'colander.tests:nonexisting')

    def test__pkg_resources_style_resolve_relative_startswith_colon(self):
        import colander.tests
        typ = self._makeOne(package=colander.tests)
        result = typ._pkg_resources_style(None, ':TestGlobalObject')
        self.assertEqual(result, self.__class__)

    def test__pkg_resources_style_resolve_relative_startswith_dot(self):
        import colander
        typ = self._makeOne(package=colander)
        result = typ._pkg_resources_style(None, '.tests:TestGlobalObject')
        self.assertEqual(result, self.__class__)

    def test__pkg_resources_style_resolve_relative_is_dot(self):
        import colander.tests
        typ = self._makeOne(package=colander.tests)
        result = typ._pkg_resources_style(None, '.')
        self.assertEqual(result, colander.tests)
        
    def test__pkg_resources_style_resolve_relative_nocurrentpackage(self):
        typ = self._makeOne()
        import colander
        self.assertRaises(colander.Invalid, typ._pkg_resources_style, None,
                          '.whatever')

    def test__pkg_resources_style_irrresolveable_relative(self):
        import colander.tests
        typ = self._makeOne(package=colander)
        self.assertRaises(ImportError, typ._pkg_resources_style, None,
                          ':notexisting')

    def test_deserialize_not_a_string(self):
        typ = self._makeOne()
        e = invalid_exc(typ.deserialize, None, None)
        self.assertEqual(e.msg, '"None" is not a string')

    def test_deserialize_using_pkgresources_style(self):
        typ = self._makeOne()
        result = typ.deserialize(None, 'colander.tests:TestGlobalObject')
        self.assertEqual(result, self.__class__)

    def test_deserialize_using_zope_dottedname_style(self):
        typ = self._makeOne()
        result = typ.deserialize(None, 'colander.tests.TestGlobalObject')
        self.assertEqual(result, self.__class__)

    def test_deserialize_style_raises(self):
        typ = self._makeOne()
        e = invalid_exc(typ.deserialize, None, 'cant.be.found')
        self.assertEqual(e.msg,
                         'The dotted name "cant.be.found" cannot be imported')

    def test_serialize_ok(self):
        import colander.tests
        typ = self._makeOne()
        result = typ.serialize(None, colander.tests)
        self.assertEqual(result, 'colander.tests')
        
    def test_serialize_fail(self):
        typ = self._makeOne()
        e = invalid_exc(typ.serialize, None, None)
        self.assertEqual(e.msg, 'None has no __name__')

class TestDateTime(unittest.TestCase):
    def _makeOne(self, *arg, **kw):
        from colander import DateTime
        return DateTime(*arg, **kw)

    def test_ctor_default_tzinfo_None(self):
        import iso8601
        typ = self._makeOne()
        self.assertEqual(typ.default_tzinfo.__class__, iso8601.iso8601.Utc)

    def test_ctor_default_tzinfo_non_None(self):
        import iso8601
        tzinfo = iso8601.iso8601.FixedOffset(1, 0, 'myname')
        typ = self._makeOne(default_tzinfo=tzinfo)
        self.assertEqual(typ.default_tzinfo, tzinfo)

    def test_serialize_with_garbage(self):
        typ = self._makeOne()
        node = DummySchemaNode(None)
        e = invalid_exc(typ.serialize, node, 'garbage')
        self.assertEqual(e.msg, "'garbage' is not a datetime object")

    def test_serialize_with_date(self):
        import datetime
        typ = self._makeOne()
        date = datetime.date.today()
        node = DummySchemaNode(None)
        result = typ.serialize(node, date)
        expected = datetime.datetime.combine(date, datetime.time())
        expected = expected.replace(tzinfo=typ.default_tzinfo).isoformat()
        self.assertEqual(result, expected)

    def test_serialize_with_naive_datetime(self):
        import datetime
        typ = self._makeOne()
        dt = datetime.datetime.now()
        node = DummySchemaNode(None)
        result = typ.serialize(node, dt)
        expected = dt.replace(tzinfo=typ.default_tzinfo).isoformat()
        self.assertEqual(result, expected)

    def test_serialize_with_tzware_datetime(self):
        import datetime
        import iso8601
        typ = self._makeOne()
        dt = datetime.datetime.now()
        tzinfo = iso8601.iso8601.FixedOffset(1, 0, 'myname')
        dt = dt.replace(tzinfo=tzinfo)
        node = DummySchemaNode(None)
        result = typ.serialize(node, dt)
        expected = dt.isoformat()
        self.assertEqual(result, expected)

    def test_deserialize_date(self):
        import datetime
        import iso8601
        date = datetime.date.today()
        typ = self._makeOne()
        formatted = date.isoformat()
        node = DummySchemaNode(None)
        result = typ.deserialize(node, formatted)
        expected = datetime.datetime.combine(result, datetime.time())
        tzinfo = iso8601.iso8601.Utc()
        expected = expected.replace(tzinfo=tzinfo)
        self.assertEqual(result.isoformat(), expected.isoformat())

    def test_deserialize_invalid_ParseError(self):
        node = DummySchemaNode(None)
        typ = self._makeOne()
        e = invalid_exc(typ.deserialize, node, 'garbage')
        self.failUnless('cannot be parsed' in e.msg)

    def test_deserialize_success(self):
        import datetime
        import iso8601
        typ = self._makeOne()
        dt = datetime.datetime.now()
        tzinfo = iso8601.iso8601.FixedOffset(1, 0, 'myname')
        dt = dt.replace(tzinfo=tzinfo)
        iso = dt.isoformat()
        node = DummySchemaNode(None)
        result = typ.deserialize(node, iso)
        self.assertEqual(result.isoformat(), iso)
        
class TestDate(unittest.TestCase):
    def _makeOne(self, *arg, **kw):
        from colander import Date
        return Date(*arg, **kw)

    def test_serialize_with_garbage(self):
        typ = self._makeOne()
        node = DummySchemaNode(None)
        e = invalid_exc(typ.serialize, node, 'garbage')
        self.assertEqual(e.msg, "'garbage' is not a date object")

    def test_serialize_with_date(self):
        import datetime
        typ = self._makeOne()
        date = datetime.date.today()
        node = DummySchemaNode(None)
        result = typ.serialize(node, date)
        expected = date.isoformat()
        self.assertEqual(result, expected)

    def test_serialize_with_datetime(self):
        import datetime
        typ = self._makeOne()
        dt = datetime.datetime.now()
        node = DummySchemaNode(None)
        result = typ.serialize(node, dt)
        expected = dt.date().isoformat()
        self.assertEqual(result, expected)

    def test_deserialize_invalid_ParseError(self):
        node = DummySchemaNode(None)
        typ = self._makeOne()
        e = invalid_exc(typ.deserialize, node, 'garbage')
        self.failUnless('cannot be parsed' in e.msg)

    def test_deserialize_invalid_weird(self):
        node = DummySchemaNode(None)
        typ = self._makeOne()
        e = invalid_exc(typ.deserialize, node, '10-10-10-10')
        self.failUnless('cannot be parsed' in e.msg)

    def test_deserialize_success_date(self):
        import datetime
        typ = self._makeOne()
        date = datetime.date.today()
        iso = date.isoformat()
        node = DummySchemaNode(None)
        result = typ.deserialize(node, iso)
        self.assertEqual(result.isoformat(), iso)

    def test_deserialize_success_datetime(self):
        import datetime
        dt = datetime.datetime.now()
        typ = self._makeOne()
        iso = dt.isoformat()
        node = DummySchemaNode(None)
        result = typ.deserialize(node, iso)
        self.assertEqual(result.isoformat(), dt.date().isoformat())

class TestSchemaNode(unittest.TestCase):
    def _makeOne(self, *arg, **kw):
        from colander import SchemaNode
        return SchemaNode(*arg, **kw)

    def test_new_sets_order(self):
        node = self._makeOne(None)
        self.failUnless(hasattr(node, '_order'))

    def test_ctor_no_title(self):
        node = self._makeOne(None, 0, validator=1, default=2, name='name')
        self.assertEqual(node.typ, None)
        self.assertEqual(node.children, [0])
        self.assertEqual(node.validator, 1)
        self.assertEqual(node.default, 2)
        self.assertEqual(node.name, 'name')
        self.assertEqual(node.title, 'Name')

    def test_ctor_with_title(self):
        node = self._makeOne(None, 0, validator=1, default=2, name='name',
                             title='title')
        self.assertEqual(node.typ, None)
        self.assertEqual(node.children, [0])
        self.assertEqual(node.validator, 1)
        self.assertEqual(node.default, 2)
        self.assertEqual(node.name, 'name')
        self.assertEqual(node.title, 'title')

    def test_ctor_with_description(self):
        node = self._makeOne(None, 0, validator=1, default=2, name='name',
                             title='title', description='desc')
        self.assertEqual(node.description, 'desc')

    def test_required_true(self):
        node = self._makeOne(None)
        self.assertEqual(node.required, True)

    def test_required_false(self):
        node = self._makeOne(None, default=1)
        self.assertEqual(node.required, False)

    def test_sdefault_missing(self):
        node = self._makeOne(None)
        self.assertEqual(node.sdefault, None)

    def test_sdefault_not_missing(self):
        typ = DummyType()
        node = self._makeOne(typ, default=1)
        self.assertEqual(node.sdefault, 1)

    def test_deserialize_no_validator(self):
        typ = DummyType()
        node = self._makeOne(typ)
        result = node.deserialize(1)
        self.assertEqual(result, 1)

    def test_deserialize_with_validator(self):
        typ = DummyType()
        validator = DummyValidator(msg='Wrong')
        node = self._makeOne(typ, validator=validator)
        e = invalid_exc(node.deserialize, 1)
        self.assertEqual(e.msg, 'Wrong')

    def test_serialize(self):
        typ = DummyType()
        node = self._makeOne(typ)
        result = node.serialize(1)
        self.assertEqual(result, 1)

    def test_add(self):
        node = self._makeOne(None)
        node.add(1)
        self.assertEqual(node.children, [1])

    def test_repr(self):
        node = self._makeOne(None, name='flub')
        result = repr(node)
        self.failUnless(result.startswith('<SchemaNode object at '))
        self.failUnless(result.endswith("named 'flub'>"))

    def test___getitem__success(self):
        node = self._makeOne(None)
        another = self._makeOne(None, name='another')
        node.add(another)
        self.assertEqual(node['another'], another)
        
    def test___getitem__failure(self):
        node = self._makeOne(None)
        self.assertRaises(KeyError, node.__getitem__, 'another')

    def test_clone(self):
        inner_typ = DummyType()
        outer_typ = DummyType()
        outer_node = self._makeOne(outer_typ, name='outer')
        inner_node = self._makeOne(inner_typ, name='inner')
        outer_node.foo = 1
        inner_node.foo = 2
        outer_node.children = [inner_node]
        outer_clone = outer_node.clone()
        self.failIf(outer_clone is outer_node)
        self.assertEqual(outer_clone.typ, outer_typ)
        self.assertEqual(outer_clone.name, 'outer')
        self.assertEqual(outer_node.foo, 1)
        self.assertEqual(len(outer_clone.children), 1)
        inner_clone = outer_clone.children[0]
        self.failIf(inner_clone is inner_node)
        self.assertEqual(inner_clone.typ, inner_typ)
        self.assertEqual(inner_clone.name, 'inner')
        self.assertEqual(inner_clone.foo, 2)

class TestSchema(unittest.TestCase):
    def test_alias(self):
        from colander import Schema
        from colander import MappingSchema
        self.assertEqual(Schema, MappingSchema)

    def test_it(self):
        import colander
        class MySchema(colander.Schema):
            thing = colander.SchemaNode(colander.String())
            thing2 = colander.SchemaNode(colander.String(), title='bar')
        node = MySchema(default='abc')
        self.failUnless(hasattr(node, '_order'))
        self.assertEqual(node.default, 'abc')
        self.assertEqual(node.__class__, colander.SchemaNode)
        self.assertEqual(node.typ.__class__, colander.Mapping)
        self.assertEqual(node.children[0].typ.__class__, colander.String) 
        self.assertEqual(node.children[0].title, 'Thing')
        self.assertEqual(node.children[1].title, 'bar')
        
class TestSequenceSchema(unittest.TestCase):
    def test_it(self):
        import colander
        _inner = colander.SchemaNode(colander.String())
        class MySchema(colander.SequenceSchema):
            inner = _inner
        node = MySchema()
        self.failUnless(hasattr(node, '_order'))
        self.assertEqual(node.__class__, colander.SchemaNode)
        self.assertEqual(node.typ.__class__, colander.Sequence)
        self.assertEqual(node.children[0], _inner)

class TestTupleSchema(unittest.TestCase):
    def test_it(self):
        import colander
        class MySchema(colander.TupleSchema):
            thing = colander.SchemaNode(colander.String())
        node = MySchema()
        self.failUnless(hasattr(node, '_order'))
        self.assertEqual(node.__class__, colander.SchemaNode)
        self.assertEqual(node.typ.__class__, colander.Tuple)
        self.assertEqual(node.children[0].typ.__class__, colander.String)

class TestFunctional(object):
    def test_deserialize_ok(self):
        import colander.tests
        data = {
            'int':'10',
            'ob':'colander.tests',
            'seq':[('1', 's'),('2', 's'), ('3', 's'), ('4', 's')],
            'seq2':[{'key':'1', 'key2':'2'}, {'key':'3', 'key2':'4'}],
            'tup':('1', 's'),
            }
        schema = self._makeSchema()
        result = schema.deserialize(data)
        self.assertEqual(result['int'], 10)
        self.assertEqual(result['ob'], colander.tests)
        self.assertEqual(result['seq'],
                         [(1, 's'), (2, 's'), (3, 's'), (4, 's')])
        self.assertEqual(result['seq2'],
                         [{'key':1, 'key2':2}, {'key':3, 'key2':4}])
        self.assertEqual(result['tup'], (1, 's'))
        
    def test_invalid_asdict(self):
        expected = {
            'int': '20 is greater than maximum value 10',
            'ob': 'The dotted name "no.way.this.exists" cannot be imported',
            'seq.0.0': '"q" is not a number',
            'seq.1.0': '"w" is not a number',
            'seq.2.0': '"e" is not a number',
            'seq.3.0': '"r" is not a number',
            'seq2.0.key': '"t" is not a number',
            'seq2.0.key2': '"y" is not a number',
            'seq2.1.key': '"u" is not a number',
            'seq2.1.key2': '"i" is not a number',
            'tup.0': '"s" is not a number'}
        data = {
            'int':'20',
            'ob':'no.way.this.exists',
            'seq':[('q', 's'),('w', 's'), ('e', 's'), ('r', 's')],
            'seq2':[{'key':'t', 'key2':'y'}, {'key':'u', 'key2':'i'}],
            'tup':('s', 's'),
            }
        schema = self._makeSchema()
        e = invalid_exc(schema.deserialize, data)
        errors = e.asdict()
        self.assertEqual(errors, expected)

class TestImperative(unittest.TestCase, TestFunctional):
    
    def _makeSchema(self):
        import colander

        integer = colander.SchemaNode(
            colander.Integer(),
            name='int',
            validator=colander.Range(0, 10)
            )

        ob = colander.SchemaNode(
            colander.GlobalObject(package=colander),
            name='ob',
            )

        tup = colander.SchemaNode(
            colander.Tuple(),
            colander.SchemaNode(
                colander.Integer(),
                name='tupint',
                ),
            colander.SchemaNode(
                colander.String(),
                name='tupstring',
                ),
            name='tup',
            )

        seq = colander.SchemaNode(
            colander.Sequence(),
            tup,
            name='seq',
            )

        seq2 = colander.SchemaNode(
            colander.Sequence(),
            colander.SchemaNode(
                colander.Mapping(),
                colander.SchemaNode(
                    colander.Integer(),
                    name='key',
                    ),
                colander.SchemaNode(
                    colander.Integer(),
                    name='key2',
                    ),
                name='mapping',
                ),
            name='seq2',
            )

        schema = colander.SchemaNode(
            colander.Mapping(),
            integer,
            ob,
            tup,
            seq,
            seq2)

        return schema

class TestDeclarative(unittest.TestCase, TestFunctional):
    
    def _makeSchema(self):

        import colander

        class TupleSchema(colander.TupleSchema):
            tupint = colander.SchemaNode(colander.Int())
            tupstring = colander.SchemaNode(colander.String())

        class MappingSchema(colander.MappingSchema):
            key = colander.SchemaNode(colander.Int())
            key2 = colander.SchemaNode(colander.Int())

        class SequenceOne(colander.SequenceSchema):
            tuple = TupleSchema()

        class SequenceTwo(colander.SequenceSchema):
            mapping = MappingSchema()

        class MainSchema(colander.MappingSchema):
            int = colander.SchemaNode(colander.Int(),
                                     validator=colander.Range(0, 10))
            ob = colander.SchemaNode(colander.GlobalObject(package=colander))
            seq = SequenceOne()
            tup = TupleSchema()
            seq2 = SequenceTwo()

        schema = MainSchema()
        return schema

class Dummy(object):
    pass

class DummySchemaNode(object):
    def __init__(self, typ, name='', exc=None, default=None):
        self.typ = typ
        self.name = name
        self.exc = exc
        self.required = default is None
        self.default = default
        self.children = []

    def deserialize(self, val):
        from colander import Invalid
        if self.exc:
            raise Invalid(self, self.exc)
        return val

    def serialize(self, val):
        from colander import Invalid
        if self.exc:
            raise Invalid(self, self.exc)
        return val

class DummyValidator(object):
    def __init__(self, msg=None):
        self.msg = msg

    def __call__(self, node, value):
        from colander import Invalid
        if self.msg:
            raise Invalid(node, self.msg)

class Uncooperative(object):
    def __str__(self):
        raise ValueError('I wont cooperate')

    __unicode__ = __str__
    
class DummyType(object):
    def serialize(self, node, value):
        return value

    def deserialize(self, node, value):
        return value
