# -*- coding: utf-8 -*-
from lark import Transformer as LarkTransformer

from pytest import mark, raises

from storyscript.exceptions import StorySyntaxError
from storyscript.parser import Transformer, Tree


def test_transformer():
    assert issubclass(Transformer, LarkTransformer)


def test_transformer_arguments():
    assert Transformer.arguments('matches') == Tree('arguments', 'matches')


def test_transformer_arguments_short():
    matches = [Tree('path', ['token'])]
    expected = ['token', Tree('path', ['token'])]
    assert Transformer.arguments(matches) == Tree('arguments', expected)


def test_transformer_assignment(magic):
    matches = [magic()]
    assert Transformer.assignment(matches) == Tree('assignment', matches)


def test_transformer_assignment_error_backslash(patch, magic):
    patch.init(StorySyntaxError)
    token = magic(value='/')
    matches = [magic(children=[token])]
    with raises(StorySyntaxError):
        Transformer.assignment(matches)
    error = 'variables_backslash'
    StorySyntaxError.__init__.assert_called_with(error, token=token)


def test_transformer_assignment_error_dash(patch, magic):
    patch.init(StorySyntaxError)
    token = magic(value='-')
    matches = [magic(children=[token])]
    with raises(StorySyntaxError):
        Transformer.assignment(matches)
    StorySyntaxError.__init__.assert_called_with('variables_dash', token=token)


def test_transformer_service_block():
    """
    Ensures service_block nodes are transformed correctly
    """
    assert Transformer.service_block([]) == Tree('service_block', [])


def test_transformer_service_block_when(tree):
    """
    Ensures service_block nodes with a when block are transformed correctly
    """
    tree.block.rules = None
    matches = ['service_block', tree]
    result = Transformer.service_block(matches)
    assert result == Tree('service_block', matches)


def test_transformer_service_block_indented_args(tree, magic):
    """
    Ensures service_block with indented arguments are transformed correctly.
    """
    tree.find_data.return_value = ['argument']
    block = magic()
    matches = [block, tree]
    result = Transformer.service_block(matches)
    block.service_fragment.children.append.assert_called_with('argument')
    assert result == Tree('service_block', [block])


@mark.parametrize('rule', ['start', 'line', 'block', 'command', 'statement'])
def test_transformer_rules(rule):
    result = getattr(Transformer(), rule)(['matches'])
    assert isinstance(result, Tree)
    assert result.data == rule
    assert result.children == ['matches']