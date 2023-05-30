import gettext
import logging
from io import BytesIO

import streamlit as st
from babel import Locale
from babel.support import Translations
from gtts import gTTS, gTTSError
from openai import OpenAIError, InvalidRequestError
from streamlit_chat import message
from streamlit_option_menu import option_menu

from chat_bot import create_gpt_completion
APP_NAME = 'Chatbot'
PAGE_TITLE: str = APP_NAME
PAGE_ICON: str = '🤖'
BOT_NAME='Pipiolo'
LANG_EN: str = 'En'
LANG_ES: str = 'Es'
GPT_MODEL_OPTIONS: list[str] = [
    'gpt-3.5-turbo',
    'gpt-4',
    'gpt-4-32k',
]

logger = logging.getLogger()

st.set_page_config(page_title=PAGE_TITLE, page_icon=PAGE_ICON)

selected_lang = option_menu(
    menu_title=None,
    options=[LANG_EN, LANG_ES],
    icons=['globe2', 'translate'],
    menu_icon='cast',
    default_index=0,
    orientation='horizontal',
)

# Storing The Context
if 'locale' not in st.session_state:
    st.session_state.locale = 'en'
if 'generated' not in st.session_state:
    st.session_state.generated = []
if 'past' not in st.session_state:
    st.session_state.past = []
if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'user_text' not in st.session_state:
    st.session_state.user_text = ''


def clear_chat():
    st.session_state.generated = []
    st.session_state.past = []
    st.session_state.messages = []
    st.session_state.user_text = ''


def show_text_input():
    st.text_area(label=_(f'Start Your Conversation With {BOT_NAME}:'),
                 value=st.session_state.user_text,
                 key='user_text')


def show_chat_buttons():
    b0, b1, b2 = st.columns(3)
    with b0, b1, b2:
        b0.button(label=_('Send'))
        b1.button(label=_('Clear'),
                  on_click=clear_chat)
        b2.download_button(
            label=_('Save'),
            data='\\n'.join([str(d) for d in st.session_state.messages[1:]]),
            file_name='gpt_chatbots.json',
            mime='application/json',
        )


def show_messages(bot_response: str, prompt: str) -> None:
    if bot_response not in st.session_state.generated:
        st.session_state.past.append(prompt)
        st.session_state.generated.append(bot_response)
    if st.session_state.generated:
        for i in range(len(st.session_state.generated)):
            message(
                st.session_state.past[i],
                is_user=True,
                key=f'{str(i)}_user',
                avatar_style='micah',
            )
            message('', key=str(i))
            st.markdown(st.session_state.generated[i])


def interact_with_bot():
    try:
        completion = create_gpt_completion(st.session_state.model,
                                           st.session_state.temperature,
                                           st.session_state.messages)
        bot_response = completion.get('choices')[0].get('message').get('content')
        st.session_state.messages.append({'role': 'assistant', 'content': bot_response})
        if bot_response:
            show_messages(bot_response, st.session_state.user_text)
            st.divider()
            show_audio_player(bot_response)
    except InvalidRequestError as err:
        if err.code == 'context_length_exceeded':
            st.session_state.messages.pop(1)
            if len(st.session_state.messages) == 1:
                st.session_state.user_text = ''
            update()
        else:
            st.error(err)
    except (OpenAIError, UnboundLocalError) as err:
        st.error(err)


def update():
    if st.session_state.messages:
        st.session_state.messages.append({'role': 'user', 'content': st.session_state.user_text})
    else:
        bot_role = f'{st.session_state.role}. {_("Answer concisely")}'
        st.session_state.messages = [
            {'role': 'system', 'content': bot_role},
            {'role': 'user', 'content': st.session_state.user_text},
        ]
    interact_with_bot()


def show_audio_player(ai_content: str) -> None:
    sound_file = BytesIO()
    try:
        tts = gTTS(text=ai_content, lang=st.session_state.locale)
        tts.write_to_fp(sound_file)
        st.write(_('To hear the voice please Play'))
        st.audio(sound_file)
    except gTTSError as err:
        st.error(err)


def main():
    c1, c2 = st.columns(2)
    with c1, c2:
        c1.selectbox(label=_('Select Model'), key='model', options=GPT_MODEL_OPTIONS)
        c1.slider(label=_('Select temperature'), key='temperature', min_value=0.0, max_value=1.0,)
        c2.text_input(label=_('Edit Role'), key='role', value=_('You are a kind assistant'))
    if st.session_state.user_text:
        update()
        st.session_state.user_text = ''
    show_text_input()
    show_chat_buttons()


if __name__ == '__main__':
    match selected_lang:
        case 'En':
            st.session_state.locale = 'en'
            locale = Locale('en','US')
        case 'Es':
            st.session_state.locale = 'es'
            locale = Locale('es', 'ES')
        case _:
            st.session_state.locale = 'en'
            locale = Locale('en', 'US')
    print(f'Locale set to {locale}')
    translations = Translations.load('locale',st.session_state.locale)
    translations.install()
    _ = translations.gettext
    title = _('Chatbot')
    st.markdown(f'<h1 style="text-align: center;">{title}</h1>', unsafe_allow_html=True)
    main()
