"""Unit tests for prompt domain rendering."""

from promptdb.domain import (
    ChatMessage,
    FewShotBlock,
    MessagePlaceholder,
    MessageRole,
    PromptKind,
    PromptSpec,
    TemplateFormat,
    extract_variables,
    render_template,
)


def test_render_fstring_template() -> None:
    """Render an f-string style template."""
    assert render_template('Hello {name}', {'name': 'Will'}, TemplateFormat.FSTRING) == 'Hello Will'


def test_render_jinja2_template() -> None:
    """Render a Jinja2 template."""
    result = render_template(
        'Hello {{ name }}', {'name': 'Will'}, TemplateFormat.JINJA2,
    )
    assert result == 'Hello Will'


def test_render_mustache_template() -> None:
    """Render a Mustache template."""
    result = render_template(
        'Hello {{name}}', {'name': 'Will'}, TemplateFormat.MUSTACHE,
    )
    assert result == 'Hello Will'


def test_extract_variables_from_fstring() -> None:
    """Extract variables from an f-string template."""
    assert extract_variables('A {x} and {y}', TemplateFormat.FSTRING) == ['x', 'y']


def test_chat_prompt_renders_placeholders() -> None:
    """Expand runtime message placeholders in a chat prompt."""
    spec = PromptSpec(
        kind=PromptKind.CHAT,
        messages=[
            ChatMessage(role=MessageRole.SYSTEM, template='You are {persona}.'),
            MessagePlaceholder(variable_name='history', optional=True),
            ChatMessage(role=MessageRole.HUMAN, template='{question}'),
        ],
    )
    rendered = spec.render_messages(
        {
            'persona': 'an analyst',
            'question': 'What happened?',
            'history': [{'role': 'human', 'content': 'Earlier context'}],
        }
    )
    assert rendered[0]['content'] == 'You are an analyst.'
    assert rendered[1]['content'] == 'Earlier context'
    assert rendered[2]['content'] == 'What happened?'


def test_string_prompt_supports_few_shot_examples() -> None:
    """Prepend rendered examples to a string prompt."""
    spec = PromptSpec(
        kind=PromptKind.STRING,
        template='Q: {question}\nA:',
        few_shot=FewShotBlock(
            examples=[
                {'question': '2+2?', 'answer': '4'},
                {'question': 'Capital of France?', 'answer': 'Paris'},
            ],
            string_template='Q: {question}\nA: {answer}',
        ),
    )
    rendered = spec.render_text({'question': 'Color of sky?'})
    assert '2+2?' in rendered
    assert 'Capital of France?' in rendered
    assert 'Color of sky?' in rendered
