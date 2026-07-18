"""Attack flow handlers."""
from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from bot.keyboards.inline_keyboards import get_confirmation_keyboard
from bot.services.attack_service import AttackService, AttackResult
from bot.states.attack_states import AttackStates
from bot.utils.logger import setup_logger

router = Router()
logger = setup_logger()
attack_service = AttackService()


@router.callback_query(F.data == "start_attack")
async def start_attack_callback(callback: CallbackQuery, state: FSMContext) -> None:
    """Handle start attack button.

    Args:
        callback: Callback query.
        state: FSM context.
    """
    message = callback.message
    
    if message.photo:
        await message.edit_caption(
            caption="<tg-emoji emoji-id=\"5339263210765710901\">🌟</tg-emoji> <b>Введите номер телефона</b>\n\n"
            "Без знака <b>+</b>",
            parse_mode="HTML",
        )
    else:
        await message.edit_text(
            "<tg-emoji emoji-id=\"5339263210765710901\">🌟</tg-emoji> <b>Введите номер телефона</b>\n\n"
            "Без знака <b>+</b>",
            parse_mode="HTML",
        )
    await state.set_state(AttackStates.waiting_phone)
    await callback.answer()


@router.message(AttackStates.waiting_phone)
async def process_phone(message: Message, state: FSMContext) -> None:
    """Process phone number input.

    Args:
        message: Telegram message.
        state: FSM context.
    """
    phone = message.text.strip()

    if not phone.isdigit():
        await message.answer(
            "<tg-emoji emoji-id=\"5339047410133919746\">🌟</tg-emoji> "
            "Введите номер без любых символов!",
            parse_mode="HTML",
        )
        return

    await state.update_data(phone=phone)
    await message.answer(
        "<tg-emoji emoji-id=\"5339335666863989864\">🌟</tg-emoji> <b>Введите количество повторов</b>\n\n"
        "От 1 до 1000",
        parse_mode="HTML",
    )
    await state.set_state(AttackStates.waiting_repeats)


@router.message(AttackStates.waiting_repeats)
async def process_repeats(message: Message, state: FSMContext) -> None:
    """Process repeats input.

    Args:
        message: Telegram message.
        state: FSM context.
    """
    repeats_text = message.text.strip()

    if not repeats_text.isdigit():
        await message.answer(
            "<tg-emoji emoji-id=\"5339047410133919746\">🌟</tg-emoji> "
            "Введите число без любых символов!",
            parse_mode="HTML",
        )
        return

    repeats = int(repeats_text)

    if not 1 <= repeats <= 1000:
        await message.answer(
            "<tg-emoji emoji-id=\"5339047410133919746\">🌟</tg-emoji> "
            "Введите число от 1 до 1000!",
            parse_mode="HTML",
        )
        return

    await state.update_data(repeats=repeats)
    data = await state.get_data()

    await message.answer(
        (
            "<tg-emoji emoji-id=\"5332522762105810091\">🌟</tg-emoji> <b>Подтверждение атаки</b>\n\n"
            f"<tg-emoji emoji-id=\"5339263210765710901\">🌟</tg-emoji> Номер: <code>{data['phone']}</code>\n"
            f"<tg-emoji emoji-id=\"5339335666863989864\">🌟</tg-emoji> Повторов: <code>{repeats}</code>\n\n"
            "<tg-emoji emoji-id=\"5332662082254954779\">🌟</tg-emoji> После запуска атаку нельзя остановить!"
        ),
        parse_mode="HTML",
        reply_markup=get_confirmation_keyboard(),
    )
    await state.set_state(AttackStates.confirmation)


@router.callback_query(AttackStates.confirmation, F.data == "cancel_attack")
async def cancel_attack_callback(callback: CallbackQuery, state: FSMContext) -> None:
    """Handle cancel attack button.

    Args:
        callback: Callback query.
        state: FSM context.
    """
    await state.clear()
    message = callback.message
    
    if message.photo:
        await message.edit_caption(
            caption="<tg-emoji emoji-id=\"5330273431898318607\">🌟</tg-emoji> <b>Атака отменена</b>",
            parse_mode="HTML",
        )
    else:
        await message.edit_text(
            "<tg-emoji emoji-id=\"5330273431898318607\">🌟</tg-emoji> <b>Атака отменена</b>",
            parse_mode="HTML",
        )
    await callback.answer()


@router.callback_query(AttackStates.confirmation, F.data == "confirm_attack")
async def confirm_attack_callback(callback: CallbackQuery, state: FSMContext) -> None:
    """Handle confirm attack button.

    Args:
        callback: Callback query.
        state: FSM context.
    """
    message = callback.message
    
    # Check if message has photo, use edit_caption instead of edit_text
    if message.photo:
        await message.edit_caption(
            caption="<tg-emoji emoji-id=\"5332419163199660328\">🌟</tg-emoji> <b>Атака запущена...</b>\n\n"
            "<tg-emoji emoji-id=\"5339335666863989864\">🌟</tg-emoji> Пожалуйста, подождите",
            parse_mode="HTML",
        )
    else:
        await message.edit_text(
            "<tg-emoji emoji-id=\"5332419163199660328\">🌟</tg-emoji> <b>Атака запущена...</b>\n\n"
            "<tg-emoji emoji-id=\"5339335666863989864\">🌟</tg-emoji> Пожалуйста, подождите",
            parse_mode="HTML",
        )
    await callback.answer()

    data = await state.get_data()
    phone = data["phone"]
    repeats = data["repeats"]

    logger.info(f"Starting attack on {phone} with {repeats} repeats")

    try:
        attack_service.set_attack_config(use_feedback=True, attack_type="MIX")
        result: AttackResult = await attack_service.execute_attack(phone, repeats)

        logger.info(
            f"Attack completed: {result.successful} successful, {result.failed} failed"
        )

        await state.clear()
        

        report_text = (
            "<tg-emoji emoji-id=\"5339026570952598443\">🌟</tg-emoji> <b>Атака завершена</b>\n"
            "━━━━━━━━━━━━━━\n\n"
            f"<tg-emoji emoji-id=\"5339391943820469159\">🌟</tg-emoji> Всего сервисов: "
            f"<code>{result.total_services}</code>\n"
            "━━━━━━━━━━━━━━\n"
            f"<tg-emoji emoji-id=\"5339335666863989864\">🌟</tg-emoji> Время выполнения: "
            f"<code>{result.execution_time:.1f} сек</code>"
            f"{unavailable_text}"
        )

        if message.photo:
            await message.edit_caption(caption=report_text, parse_mode="HTML")
        else:
            await message.edit_text(report_text, parse_mode="HTML")
    except Exception as e:
        logger.error(f"Attack failed with error: {e}")
        await state.clear()
        if message.photo:
            await message.edit_caption(
                caption="<tg-emoji emoji-id=\"5339212659000633145\">🌟</tg-emoji> <b>Атака завершилась с ошибкой</b>\n\n"
                f"<code>{str(e)}</code>",
                parse_mode="HTML",
            )
        else:
            await message.edit_text(
                "<tg-emoji emoji-id=\"5339212659000633145\">🌟</tg-emoji> <b>Атака завершилась с ошибкой</b>\n\n"
                f"<code>{str(e)}</code>",
                parse_mode="HTML",
            )
