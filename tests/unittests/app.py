# -*- coding: utf-8 -*-
import json
import os

from pytest import fixture, raises

from storyscript.app import App
from storyscript.compiler import Compiler
from storyscript.parser import Grammar, Parser
from storyscript.story import Story


@fixture
def storypath():
    return 'test.story'


@fixture
def story_teardown(request, storypath):
    def teardown():
        os.remove(storypath)
    request.addfinalizer(teardown)


@fixture
def story(story_teardown, storypath):
    story = 'run\n\tpass'
    with open(storypath, 'w') as file:
        file.write(story)
    return story


@fixture
def read_story(patch):
    patch.object(App, 'read_story')


@fixture
def parser(patch):
    patch.init(Parser)
    patch.object(Parser, 'parse')


def test_app_read_story(story, storypath):
    """
    Ensures App.read_story reads a story
    """
    result = App.read_story(storypath)
    assert result == story


def test_app_read_story_not_found(patch, capsys):
    patch.object(os, 'path')
    with raises(SystemExit):
        App.read_story('whatever')
    out, err = capsys.readouterr()
    assert out == 'File "whatever" not found at {}\n'.format(os.path.abspath())


def test_app_get_stories(mocker):
    """
    Ensures App.get_stories returns the original path if it's not a directory
    """
    mocker.patch.object(os.path, 'isdir', return_value=False)
    assert App.get_stories('stories') == ['stories']


def test_app_get_stories_directory(mocker):
    """
    Ensures App.get_stories returns stories in a directory
    """
    mocker.patch.object(os.path, 'isdir')
    mocker.patch.object(os, 'walk',
                        return_value=[('root', [], ['one.story', 'two'])])
    assert App.get_stories('stories') == ['root/one.story']


def test_app_services():
    compiled_stories = {'a': {'services': ['one']}, 'b': {'services': ['two']}}
    result = App.services(compiled_stories)
    assert result == ['one', 'two']


def test_app_services_no_duplicates():
    compiled_stories = {'a': {'services': ['one']}, 'b': {'services': ['one']}}
    result = App.services(compiled_stories)
    assert result == ['one']


def test_app_compile(patch):
    patch.object(json, 'dumps')
    patch.object(Story, 'from_file')
    patch.many(App, ['get_stories', 'services'])
    App.get_stories.return_value = ['one.story']
    result = App.compile('path')
    App.get_stories.assert_called_with('path')
    Story.from_file.assert_called_with('one.story')
    Story.from_file().process.assert_called_with(ebnf_file=None, debug=False)
    App.services.assert_called_with({'one.story': Story.from_file().process()})
    dictionary = {'stories': {'one.story': Story.from_file().process()},
                  'services': App.services()}
    json.dumps.assert_called_with(dictionary, indent=2)
    assert result == json.dumps()


def test_app_compile_ebnf_file(patch):
    patch.object(json, 'dumps')
    patch.object(Story, 'from_file')
    patch.many(App, ['get_stories', 'services'])
    App.get_stories.return_value = ['one.story']
    App.compile('path', ebnf_file='ebnf')
    Story.from_file().process.assert_called_with(ebnf_file='ebnf', debug=False)


def test_app_compile_debug(patch):
    patch.object(json, 'dumps')
    patch.object(Story, 'from_file')
    patch.many(App, ['get_stories', 'services'])
    App.get_stories.return_value = ['one.story']
    App.compile('path', debug='debug')
    Story.from_file().process.assert_called_with(ebnf_file=None, debug='debug')


def test_app_lexer(patch):
    patch.object(Story, 'from_file')
    patch.object(App, 'get_stories', return_value=['one.story'])
    result = App.lex('/path')
    Story.from_file.assert_called_with('one.story')
    assert result == {'one.story': Story.from_file().lex()}


def test_app_grammar(patch):
    patch.init(Grammar)
    patch.object(Grammar, 'build')
    assert App.grammar() == Grammar().build()


def test_app_loads(patch):
    patch.init(Story)
    patch.object(Story, 'process')
    result = App.loads('string')
    Story.__init__.assert_called_with('string')
    assert result == Story.process()


def test_app_load(patch, magic):
    patch.object(Story, 'from_stream')
    stream = magic()
    result = App.load(stream)
    Story.from_stream.assert_called_with(stream)
    story = Story.from_stream().process()
    assert result == {stream.name: story, 'services': story['services']}
