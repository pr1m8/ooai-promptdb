"""Streamlit dashboard for :mod:`promptdb`.

Purpose:
    Provide a lightweight operator UI over the HTTP API.

Design:
    The dashboard talks to the API rather than importing repository code
    directly.

Attributes:
    main: Streamlit entry point.

Examples:
    .. code-block:: bash

        streamlit run src/promptdb/dashboard_streamlit/app.py
"""

from __future__ import annotations

import json
import os

import httpx

API_BASE = os.getenv('PROMPTDB_DASHBOARD_API_BASE', 'http://localhost:8000/api/v1')


def main() -> None:
    """Run the Streamlit dashboard.

    Args:
        None.

    Returns:
        None.

    Raises:
        httpx.HTTPError: If the API is unavailable.

    Examples:
        .. code-block:: python

            main()
    """
    import streamlit as st

    st.set_page_config(page_title='promptdb', layout='wide')
    st.title('promptdb dashboard')

    with httpx.Client(timeout=10.0) as client:
        response = client.get(f'{API_BASE}/versions')
        response.raise_for_status()
        versions = response.json()

        st.subheader('Registered prompt versions')
        if versions:
            st.dataframe(
                [
                    {
                        'namespace': row['namespace'],
                        'name': row['name'],
                        'revision': row['revision'],
                        'user_version': row.get('user_version'),
                        'aliases': ', '.join(row.get('aliases', [])),
                        'title': (row.get('spec') or {}).get('metadata', {}).get('title'),
                    }
                    for row in versions
                ],
                use_container_width=True,
            )
        else:
            st.info('No prompt versions registered yet.')

        st.subheader('Render a prompt')
        namespace = st.text_input('Namespace', value='research')
        name = st.text_input('Name', value='answerer')
        selector = st.text_input('Selector', value='latest')
        variables_text = st.text_area(
            'Variables JSON',
            value=json.dumps({'question': 'What is PACELC?'}, indent=2),
            height=140,
        )

        if st.button('Render'):
            payload = {'variables': json.loads(variables_text)}
            render_response = client.post(
                f'{API_BASE}/prompts/{namespace}/{name}/render',
                params={'selector': selector},
                json=payload,
            )
            render_response.raise_for_status()
            st.json(render_response.json())


if __name__ == '__main__':
    main()
