#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (c) 2009, Nicolas Clairon
# All rights reserved.
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
#     * Redistributions of source code must retain the above copyright
#       notice, this list of conditions and the following disclaimer.
#     * Redistributions in binary form must reproduce the above copyright
#       notice, this list of conditions and the following disclaimer in the
#       documentation and/or other materials provided with the distribution.
#     * Neither the name of the University of California, Berkeley nor the
#       names of its contributors may be used to endorse or promote products
#       derived from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE REGENTS AND CONTRIBUTORS ``AS IS'' AND ANY
# EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE REGENTS AND CONTRIBUTORS BE LIABLE FOR ANY
# DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
# ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

import unittest

from mongokit import *

class StructureTestCase(unittest.TestCase):
    def setUp(self):
        self.collection = Connection()['test']['mongokit']
        
    def tearDown(self):
        Connection()['test'].drop_collection('mongokit')

    def test_no_structure(self):
        class MyDoc(SchemaDocument): pass
        self.assertRaises(StructureError, MyDoc)

    def test_empty_structure(self):
        class MyDoc(SchemaDocument):
            structure = {}
        assert MyDoc() == {}

    def test_structure_not_dict(self):
        class MyDoc(SchemaDocument):
            structure = 3
        self.assertRaises(StructureError, MyDoc)

    def test_load_with_dict(self):
        doc = {"foo":1, "bla":{"bar":u"spam"}}
        class MyDoc(SchemaDocument):
            structure = {"foo":int, "bla":{"bar":unicode}}
        mydoc = MyDoc(doc)
        assert mydoc == doc
        mydoc.validate()
        
    def test_simple_structure(self):
        class MyDoc(SchemaDocument):
            structure = {
                "foo":unicode,
                "bar":int
            }
        assert MyDoc() == {"foo":None, "bar":None}

    def test_missed_field(self):
        doc = {"foo":u"arf"}
        class MyDoc(SchemaDocument):
            structure = {
                "foo":unicode,
                "bar":{"bla":int}
            }
        mydoc = MyDoc(doc)
        self.assertRaises(StructureError, mydoc.validate)

    def test_unknown_field(self):
        class MyDoc(SchemaDocument):
            structure = {
                "foo":unicode,
            }
        mydoc = MyDoc()
        mydoc["bar"] = 4
        self.assertRaises(StructureError, mydoc.validate)

    def test_big_nested_structure(self):
        class MyDoc(SchemaDocument):
            structure = {
                "1":{
                    "2":{
                        "3":{
                            "4":{
                                "5":{
                                    "6":{
                                        "7":int,
                                        "8":{
                                            unicode:{int:int}
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        mydoc = MyDoc()
        assert mydoc._namespaces == ['1', '1.2', '1.2.3', '1.2.3.4', '1.2.3.4.5', '1.2.3.4.5.6', '1.2.3.4.5.6.8', '1.2.3.4.5.6.8.$unicode', '1.2.3.4.5.6.8.$unicode.$int', '1.2.3.4.5.6.7']
        mydoc['1']['2']['3']['4']['5']['6']['7'] = 8
        mydoc['1']['2']['3']['4']['5']['6']['8'] = {u"bla":{3:u"bla"}}
        self.assertRaises(SchemaTypeError,  mydoc.validate)
        mydoc['1']['2']['3']['4']['5']['6']['8'] = {9:{3:10}}
        self.assertRaises(SchemaTypeError,  mydoc.validate)
        mydoc['1']['2']['3']['4']['5']['6']['8'] = {u"bla":{3:4}}
        mydoc.validate()
            
    def test_dot_notation(self):
        class MyDoc(SchemaDocument):
            use_dot_notation = True
            structure = {
                "foo":int,
                "bar":unicode
            }

        mydoc = MyDoc()
        mydoc.foo = "3"
        self.assertRaises(SchemaTypeError, mydoc.validate)
        mydoc.foo = 3
        assert mydoc['foo'] == 3
        assert mydoc == {'foo':3, 'bar':None}
        mydoc.validate()
        mydoc.bar = u"bar"
        assert mydoc == {'foo':3, 'bar':'bar'}
        mydoc.validate()
        
    def test_dot_notation_nested(self):
        class MyDoc(SchemaDocument):
            use_dot_notation = True
            structure = {
                "foo":{
                    "bar":unicode
                }
            }

        mydoc = MyDoc()
        mydoc.foo.bar = 3
        self.assertRaises(SchemaTypeError, mydoc.validate)
        mydoc.foo.bar = u"bar"
        assert mydoc.foo.bar == u'bar'
        mydoc.foo.bla = 2
        assert mydoc.foo.bla == 2
        assert mydoc['foo'] == {"bar":"bar"}, mydoc
        assert mydoc['foo']['bar'] == 'bar'
        assert mydoc == {'foo':{'bar':'bar'}}
        mydoc.validate()

    def test_dot_notation_field_not_in_structure(self):
        class MyDoc(SchemaDocument):
            use_dot_notation = True
            structure = {
                "foo":{
                    "bar":unicode,
                },
                "spam":int,
            }

        mydoc = MyDoc()
        mydoc.eggs = 4
        assert mydoc == {'foo':{'bar':None}, 'spam':None}
        assert mydoc.eggs == 4
        try:
            mydoc.not_found
        except AttributeError, e:
            print str(e)
        mydoc.foo.eggs = 4
        assert mydoc == {'foo':{'bar':None}, 'spam':None}, mydoc
        mydoc.validate()

