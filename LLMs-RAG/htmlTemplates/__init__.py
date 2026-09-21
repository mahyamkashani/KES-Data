"""HTML/CSS templates for the Streamlit chat UI.

Provides the three names ``categorize_reports.py`` imports: ``css`` (injected
once via ``st.write(..., unsafe_allow_html=True)``) and the two message
templates, whose ``{{MSG}}`` placeholder is replaced with the message content.
"""

__all__ = ["css", "user_template", "bot_template"]

css = '''
<style>
.chat-message {
    padding: 1.5rem; border-radius: 0.5rem; margin-bottom: 1rem; display: flex;
}
.chat-message.user {
    background-color: #2b313e;
}
.chat-message.bot {
    background-color: #475063;
}
.chat-message .avatar {
    width: 15%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 2rem;
}
.chat-message .message {
    width: 85%;
    padding: 0 1.5rem;
    color: #fff;
}
</style>
'''

user_template = '''
<div class="chat-message user">
    <div class="avatar">&#128100;</div>
    <div class="message">{{MSG}}</div>
</div>
'''

bot_template = '''
<div class="chat-message bot">
    <div class="avatar">&#129302;</div>
    <div class="message">{{MSG}}</div>
</div>
'''
