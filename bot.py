import os
import telebot
from telebot import types
from logic import DB_Manager
from config import TOKEN, DATABASE

bot = telebot.TeleBot(TOKEN)
manager = DB_Manager(DATABASE)

PHOTOS_DIR = 'project_photos'
if not os.path.exists(PHOTOS_DIR):
    os.makedirs(PHOTOS_DIR)

cancel_button = "🚫 Отмена"


def cansel(message):
    bot.send_message(
        message.chat.id,
        "❌ Действие отменено. Чтобы посмотреть команды, введите /info",
        reply_markup=types.ReplyKeyboardRemove()
    )


def no_projects(message):
    bot.send_message(
        message.chat.id,
        "📭 У тебя пока нет проектов!\nМожешь добавить первый с помощью команды /new_project 🚀"
    )


def gen_inline_markup(rows):
    markup = types.InlineKeyboardMarkup()
    markup.row_width = 1
    for row in rows:
        markup.add(types.InlineKeyboardButton(row, callback_data=row))
    return markup


def gen_markup(rows):
    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    markup.row_width = 1
    for row in rows:
        markup.add(types.KeyboardButton(row))
    markup.add(types.KeyboardButton(cancel_button))
    return markup


attributes_of_projects = {
    '📝 Имя проекта': ["Введите новое имя проекта:", "project_name"],
    '📄 Описание': ["Введите описание проекта:", "description"],
    '🔗 Ссылка': ["Введите новую ссылку на проект:", "url"],
    '📊 Статус': ["Выберите новый статус задачи:", "status_id"],
    '🖼 Фото проекта': ["Отправьте фотографию (скриншот) проекта:", "photo"]
}


def info_project(message, user_id, project_name):
    info = manager.get_project_info(user_id, project_name)
    if not info:
        bot.send_message(message.chat.id, "⚠️ Проект не найден.")
        return

    project = info[0]
    skills = manager.get_project_skills(project_name)
    if not skills:
        skills = 'навыки пока не добавлены'

    description = project[1] if project[1] else 'описание пока не добавлено'
    photo_filename = project[4] if len(project) > 4 else None

    text = (
        f"🚀 <b>Проект: {project[0]}</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"📄 <b>Описание:</b> {description}\n"
        f"🔗 <b>Ссылка:</b> {project[2]}\n"
        f"📊 <b>Статус:</b> {project[3]}\n"
        f"🛠 <b>Навыки:</b> <code>{skills}</code>\n"
        f"━━━━━━━━━━━━━━━━━━━━"
    )

    if photo_filename:
        photo_path = os.path.join(PHOTOS_DIR, photo_filename)
        if os.path.exists(photo_path):
            with open(photo_path, 'rb') as photo_file:
                bot.send_photo(message.chat.id, photo_file, caption=text, parse_mode='HTML')
                return

    bot.send_message(message.chat.id, text, parse_mode='HTML')


@bot.message_handler(commands=['start'])
def start_command(message):
    bot.send_message(
        message.chat.id,
        f"👋 Привет, <b>{message.from_user.first_name}</b>! Я бот-менеджер проектов 💼\n"
        "Помогу тебе сохранить твои проекты, скриншоты и информацию о них! ✨",
        parse_mode='HTML'
    )
    info(message)


@bot.message_handler(commands=['info'])
def info(message):
    bot.send_message(
        message.chat.id,
        "📚 <b>Вот команды, которые могут тебе помочь:</b>\n\n"
        "🔹 /start — перезапустить бота и увидеть приветствие\n"
        "🔹 /info — показать эту подробную справку по командам\n"
        "🔹 /new_project — добавить новый проект в портфолио\n"
        "🔹 /projects — показать список всех твоих проектов\n"
        "🔹 /add_description — задать или изменить описание проекта\n"
        "🔹 /add_photo — прикрепить фотографию (скриншот) к проекту\n"
        "🔹 /skills — привязать навык (технологию) к проекту\n"
        "🔹 /update_projects — изменить любые данные существующего проекта\n"
        "🔹 /delete — удалить проект из базы данных\n\n"
        "⚙️ <b>Управление справочниками БД:</b>\n"
        "🔸 /add_skill — добавить новый навык в общий список\n"
        "🔸 /update_skill — переименовать навык в общем списке\n"
        "🔸 /add_status — добавить новый статус в общий список\n"
        "🔸 /update_status — переименовать статус в общем списке\n\n"
        "💡 <i>Также ты можешь просто написать имя проекта в чат, и я покажу всю информацию о нём!</i>",
        parse_mode='HTML'
    )


@bot.message_handler(commands=['new_project'])
def addtask_command(message):
    bot.send_message(message.chat.id, "✨ Введите <b>название</b> проекта:", parse_mode='HTML')
    bot.register_next_step_handler(message, name_project)


def name_project(message):
    if message.text == cancel_button:
        cansel(message)
        return
    name = message.text
    user_id = message.from_user.id
    data = [user_id, name]
    bot.send_message(message.chat.id, "🔗 Введите <b>ссылку</b> на проект:", parse_mode='HTML')
    bot.register_next_step_handler(message, link_project, data=data)


def link_project(message, data):
    if message.text == cancel_button:
        cansel(message)
        return
    data.append(message.text)
    statuses = [x[0] for x in manager.get_statuses()]
    bot.send_message(
        message.chat.id,
        "📊 Введите текущий <b>статус</b> проекта:",
        parse_mode='HTML',
        reply_markup=gen_markup(statuses)
    )
    bot.register_next_step_handler(message, callback_project, data=data)


def callback_project(message, data):
    if message.text == cancel_button:
        cansel(message)
        return
    status = message.text
    status_id = manager.get_status_id(status)
    if not status_id:
        bot.send_message(message.chat.id, "⚠️ Такого статуса нет в списке. Попробуйте снова через /new_project.")
        return

    data.append(status_id)
    manager.insert_project([tuple(data)])
    project_name = data[1]

    bot.send_message(
        message.chat.id,
        f"✅ Проект <b>«{project_name}»</b> сохранен!\n\n"
        f"📝 Хотите сразу добавить к нему <b>описание</b>? Напишите его ниже или нажмите «{cancel_button}»:",
        parse_mode='HTML',
        reply_markup=gen_markup([])
    )
    bot.register_next_step_handler(message, save_description_step, project_name=project_name)


@bot.message_handler(commands=['add_description'])
def add_description_command(message):
    user_id = message.from_user.id
    projects = manager.get_projects(user_id)
    if projects:
        project_names = [x[2] for x in projects]
        bot.send_message(
            message.chat.id,
            "📄 Выберите проект, для которого хотите задать описание:",
            reply_markup=gen_markup(project_names)
        )
        bot.register_next_step_handler(message, ask_description_step, projects=project_names)
    else:
        no_projects(message)


def ask_description_step(message, projects):
    if message.text == cancel_button:
        cansel(message)
        return
    project_name = message.text
    if project_name not in projects:
        bot.send_message(message.chat.id, "⚠️ Выберите проект с кнопок:", reply_markup=gen_markup(projects))
        bot.register_next_step_handler(message, ask_description_step, projects=projects)
        return

    bot.send_message(
        message.chat.id,
        f"✍️ Введите описание для проекта <b>«{project_name}»</b>:",
        parse_mode='HTML',
        reply_markup=gen_markup([])
    )
    bot.register_next_step_handler(message, save_description_step, project_name=project_name)


def save_description_step(message, project_name):
    if message.text == cancel_button:
        cansel(message)
        return
    user_id = message.from_user.id
    manager.update_projects("description", (message.text, project_name, user_id))
    bot.send_message(
        message.chat.id,
        f"✅ Описание для проекта <b>«{project_name}»</b> успешно сохранено!",
        parse_mode='HTML',
        reply_markup=types.ReplyKeyboardRemove()
    )


@bot.message_handler(commands=['add_photo'])
def add_photo_command(message):
    user_id = message.from_user.id
    projects = manager.get_projects(user_id)
    if projects:
        project_names = [x[2] for x in projects]
        bot.send_message(
            message.chat.id,
            "🖼 Выберите проект, к которому хотите прикрепить фото:",
            reply_markup=gen_markup(project_names)
        )
        bot.register_next_step_handler(message, ask_photo_step, projects=project_names)
    else:
        no_projects(message)


def ask_photo_step(message, projects):
    if message.text == cancel_button:
        cansel(message)
        return
    project_name = message.text
    if project_name not in projects:
        bot.send_message(message.chat.id, "⚠️ Выберите проект с кнопок:", reply_markup=gen_markup(projects))
        bot.register_next_step_handler(message, ask_photo_step, projects=projects)
        return

    bot.send_message(
        message.chat.id,
        "📸 Отправьте фотографию (скриншот) проекта:",
        reply_markup=gen_markup([])
    )
    bot.register_next_step_handler(message, save_photo_step, project_name=project_name)


def save_photo_step(message, project_name):
    if message.text == cancel_button:
        cansel(message)
        return
    if not message.photo:
        bot.send_message(
            message.chat.id,
            "⚠️ Пожалуйста, отправьте именно фотографию (картинку)!",
            reply_markup=gen_markup([])
        )
        bot.register_next_step_handler(message, save_photo_step, project_name=project_name)
        return

    user_id = message.from_user.id
    file_info = bot.get_file(message.photo[-1].file_id)
    downloaded_file = bot.download_file(file_info.file_path)

    file_ext = file_info.file_path.split('.')[-1]
    filename = f"{user_id}_{file_info.file_unique_id}.{file_ext}"
    save_path = os.path.join(PHOTOS_DIR, filename)

    with open(save_path, 'wb') as new_file:
        new_file.write(downloaded_file)

        manager.update_projects("photo", (filename, project_name, user_id))
    bot.send_message(
        message.chat.id,
        f"✅ Фотография сохранена на диск и прикреплена к проекту <b>«{project_name}»</b>!",
        parse_mode='HTML',
        reply_markup=types.ReplyKeyboardRemove()
    )


@bot.message_handler(commands=['projects'])
def get_projects(message):
    user_id = message.from_user.id
    projects = manager.get_projects(user_id)
    if projects:
        text = "\n".join([f"🔹 <b>{x[2]}</b> — {x[4]}" for x in projects])
        bot.send_message(
            message.chat.id,
            f"📂 <b>Твои проекты:</b>\n\n{text}\n\n👇 Нажми на проект, чтобы открыть его карточку:",
            parse_mode='HTML',
            reply_markup=gen_inline_markup([x[2] for x in projects])
        )
    else:
        no_projects(message)


@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    project_name = call.data
    user_id = call.from_user.id
    bot.answer_callback_query(call.id)
    info_project(call.message, user_id, project_name)


@bot.message_handler(commands=['skills'])
def skill_handler(message):
    user_id = message.from_user.id
    projects = manager.get_projects(user_id)
    if projects:
        projects = [x[2] for x in projects]
        bot.send_message(message.chat.id, "🛠 Выберите проект, для которого нужно выбрать навык:", reply_markup=gen_markup(projects))
        bot.register_next_step_handler(message, skill_project, projects=projects)
    else:
        no_projects(message)


def skill_project(message, projects):
    if message.text == cancel_button:
        cansel(message)
        return
    project_name = message.text
    if project_name not in projects:
        bot.send_message(message.chat.id, "⚠️ У тебя нет такого проекта, попробуй еще раз!", reply_markup=gen_markup(projects))
        bot.register_next_step_handler(message, skill_project, projects=projects)
        return
    skills = [x[1] for x in manager.get_skills()]
    bot.send_message(message.chat.id, "💡 Выберите навык:", reply_markup=gen_markup(skills))
    bot.register_next_step_handler(message, set_skill, project_name=project_name, skills=skills)


def set_skill(message, project_name, skills):
    if message.text == cancel_button:
        cansel(message)
        return
    skill = message.text
    user_id = message.from_user.id
    if skill not in skills:
        bot.send_message(message.chat.id, "⚠️ Видимо, ты выбрал навык не из списка, попробуй еще раз!", reply_markup=gen_markup(skills))
        bot.register_next_step_handler(message, set_skill, project_name=project_name, skills=skills)
        return
    manager.insert_skill(user_id, project_name, skill)
    bot.send_message(message.chat.id, f"✅ Навык <b>{skill}</b> добавлен проекту <b>«{project_name}»</b>!", parse_mode='HTML')


@bot.message_handler(commands=['update_projects'])
def update_project(message):
    user_id = message.from_user.id
    projects = manager.get_projects(user_id)
    if projects:
        projects = [x[2] for x in projects]
        bot.send_message(message.chat.id, "✏️ Выберите проект, который хотите изменить:", reply_markup=gen_markup(projects))
        bot.register_next_step_handler(message, update_project_step_2, projects=projects)
    else:
        no_projects(message)


def update_project_step_2(message, projects):
    if message.text == cancel_button:
        cansel(message)
        return
    project_name = message.text
    if project_name not in projects:
        bot.send_message(message.chat.id, "⚠️ Что-то пошло не так! Выберите проект заново:", reply_markup=gen_markup(projects))
        bot.register_next_step_handler(message, update_project_step_2, projects=projects)
        return
    bot.send_message(message.chat.id, "⚙️ Выберите, что требуется изменить в проекте:", reply_markup=gen_markup(attributes_of_projects.keys()))
    bot.register_next_step_handler(message, update_project_step_3, project_name=project_name)


def update_project_step_3(message, project_name):
    if message.text == cancel_button:
        cansel(message)
        return
    attribute = message.text
    reply_markup = None
    if attribute not in attributes_of_projects.keys():
        bot.send_message(message.chat.id, "⚠️ Кажется, ты ошибся, попробуй еще раз!", reply_markup=gen_markup(attributes_of_projects.keys()))
        bot.register_next_step_handler(message, update_project_step_3, project_name=project_name)
        return

    prompt_text, db_column = attributes_of_projects[attribute]
    if db_column == "status_id":
        rows = manager.get_statuses()
        reply_markup = gen_markup([x[0] for x in rows])
    elif db_column == "photo":
        bot.send_message(message.chat.id, prompt_text, reply_markup=gen_markup([]))
        bot.register_next_step_handler(message, save_photo_step, project_name=project_name)
        return

    bot.send_message(message.chat.id, prompt_text, reply_markup=reply_markup)
    bot.register_next_step_handler(message, update_project_step_4, project_name=project_name, attribute=db_column)


def update_project_step_4(message, project_name, attribute):
    if message.text == cancel_button:
        cansel(message)
        return
    update_info = message.text
    if attribute == "status_id":
        rows = manager.get_statuses()
        if update_info in [x[0] for x in rows]:
            update_info = manager.get_status_id(update_info)
        else:
            bot.send_message(message.chat.id, "⚠️ Был выбран неверный статус, попробуйте еще раз!", reply_markup=gen_markup([x[0] for x in rows]))
            bot.register_next_step_handler(message, update_project_step_4, project_name=project_name, attribute=attribute)
            return

    user_id = message.from_user.id
    data = (update_info, project_name, user_id)
    manager.update_projects(attribute, data)
    bot.send_message(message.chat.id, "✅ Готово! Обновления внесены!")


@bot.message_handler(commands=['delete'])
def delete_handler(message):
    user_id = message.from_user.id
    projects = manager.get_projects(user_id)
    if projects:
        text = "\n".join([f"🗑 <b>{x[2]}</b> — {x[4]}" for x in projects])
        projects = [x[2] for x in projects]
        bot.send_message(message.chat.id, f"{text}\n\nВыберите проект для удаления:", parse_mode='HTML', reply_markup=gen_markup(projects))
        bot.register_next_step_handler(message, delete_project, projects=projects)
    else:
        no_projects(message)


def delete_project(message, projects):
    if message.text == cancel_button:
        cansel(message)
        return
    project = message.text
    user_id = message.from_user.id
    if project not in projects:
        bot.send_message(message.chat.id, "⚠️ У тебя нет такого проекта, попробуй выбрать еще раз!", reply_markup=gen_markup(projects))
        bot.register_next_step_handler(message, delete_project, projects=projects)
        return
    project_id = manager.get_project_id(project, user_id)
    manager.delete_project(user_id, project_id)
    bot.send_message(message.chat.id, f"🗑 Проект <b>«{project}»</b> удален!", parse_mode='HTML')


@bot.message_handler(commands=['add_skill'])
def add_skill_cmd(message):
    bot.send_message(message.chat.id, "💡 Введите название нового навыка:", reply_markup=gen_markup([]))
    bot.register_next_step_handler(message, save_new_skill_cmd)


def save_new_skill_cmd(message):
    if message.text == cancel_button:
        cansel(message)
        return
    manager.insert_new_skill(message.text.strip())
    bot.send_message(message.chat.id, f"✅ Навык <b>«{message.text.strip()}»</b> добавлен в БД!", parse_mode='HTML')


@bot.message_handler(commands=['update_skill'])
def update_skill_cmd(message):
    skills = [x[1] for x in manager.get_skills()]
    bot.send_message(message.chat.id, "✏️ Выберите навык для изменения:", reply_markup=gen_markup(skills))
    bot.register_next_step_handler(message, ask_updated_skill_cmd, skills=skills)


def ask_updated_skill_cmd(message, skills):
    if message.text == cancel_button:
        cansel(message)
        return
    if message.text not in skills:
        bot.send_message(message.chat.id, "⚠️ Выберите навык с кнопок:", reply_markup=gen_markup(skills))
        bot.register_next_step_handler(message, ask_updated_skill_cmd, skills=skills)
        return
    bot.send_message(message.chat.id, f"Введите новое название для навыка «{message.text}»:")
    bot.register_next_step_handler(message, save_updated_skill_cmd, old_skill=message.text)


def save_updated_skill_cmd(message, old_skill):
    if message.text == cancel_button:
        cansel(message)
        return
    manager.update_skill(old_skill, message.text.strip())
    bot.send_message(message.chat.id, f"✅ Навык обновлен на <b>«{message.text.strip()}»</b>!", parse_mode='HTML')


@bot.message_handler(commands=['add_status'])
def add_status_cmd(message):
    bot.send_message(message.chat.id, "📊 Введите название нового статуса:", reply_markup=gen_markup([]))
    bot.register_next_step_handler(message, save_new_status_cmd)


def save_new_status_cmd(message):
    if message.text == cancel_button:
        cansel(message)
        return
    manager.insert_new_status(message.text.strip())
    bot.send_message(message.chat.id, f"✅ Статус <b>«{message.text.strip()}»</b> добавлен в БД!", parse_mode='HTML')


@bot.message_handler(commands=['update_status'])
def update_status_cmd(message):
    statuses = [x[0] for x in manager.get_statuses()]
    bot.send_message(message.chat.id, "✏️ Выберите статус для изменения:", reply_markup=gen_markup(statuses))
    bot.register_next_step_handler(message, ask_updated_status_cmd, statuses=statuses)


def ask_updated_status_cmd(message, statuses):
    if message.text == cancel_button:
        cansel(message)
        return
    if message.text not in statuses:
        bot.send_message(message.chat.id, "⚠️ Выберите статус с кнопок:", reply_markup=gen_markup(statuses))
        bot.register_next_step_handler(message, ask_updated_status_cmd, statuses=statuses)
        return
    bot.send_message(message.chat.id, f"Введите новое название для статуса «{message.text}»:")
    bot.register_next_step_handler(message, save_updated_status_cmd, old_status=message.text)


def save_updated_status_cmd(message, old_status):
    if message.text == cancel_button:
        cansel(message)
        return
    manager.update_status(old_status, message.text.strip())
    bot.send_message(message.chat.id, f"✅ Статус обновлен на <b>«{message.text.strip()}»</b>!", parse_mode='HTML')


@bot.message_handler(func=lambda message: True)
def text_handler(message):
    user_id = message.from_user.id
    projects = [x[2] for x in manager.get_projects(user_id)]
    project = message.text
    if project in projects:
        info_project(message, user_id, project)
        return
    bot.reply_to(message, "🤔 Тебе нужна помощь? Нажми /info, чтобы посмотреть список команд!")


if __name__ == '__main__':
    manager.create_tables()
    manager.default_insert()
    bot.infinity_polling()
