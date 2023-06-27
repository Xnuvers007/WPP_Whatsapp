import base64
import mimetypes
import os

from WPP_Whatsapp.api.layers.ListenerLayer import ListenerLayer


class SenderLayer(ListenerLayer):

    async def sendLinkPreview(self, chatId, url, text=''):
        """
        * Automatically sends a link with the auto generated link preview. You can also add a custom message to be added.
        * Deprecated: please use {@link sendText}
        """
        message = text if url in text else f"{text}\n{url}"
        chatId = self.valid_chatId(chatId)
        result = await self.page_evaluate("""({ chatId, message }) => {
                    return WPP.chat.sendTextMessage(chatId, message, { linkPreview: true });
                    }""", {"chatId": chatId, "message": message})
        return result

    async def sendText(self, to, content, options=None):
        """
          /**
           * Sends a text message to given chat
           * @category Chat
           * @param to chat id: xxxxx@us.c
           * @param content text message
           *
           * @example
           * ```javascript
           * // Simple message
           * client.sendText('<number>@c.us', 'A simple message');
           *
           * // With buttons
           * client.sendText('<number>@c.us', 'WPPConnect message with buttons', {
           *    useTemplateButtons: true, // False for legacy
           *    buttons: [
           *      {
           *        url: 'https://wppconnect.io/',
           *        text: 'WPPConnect Site'
           *      },
           *      {
           *        phoneNumber: '+55 11 22334455',
           *        text: 'Call me'
           *      },
           *      {
           *        id: 'your custom id 1',
           *        text: 'Some text'
           *      },
           *      {
           *        id: 'another id 2',
           *        text: 'Another text'
           *      }
           *    ],
           *    title: 'Title text' // Optional
           *    footer: 'Footer text' // Optional
           * });
           * ```
           */
        """
        if not options:
            options = {}
        to = self.valid_chatId(to)
        send_result = await self.page_evaluate("""({ to, content, options }) =>
                            WPP.chat.sendTextMessage(to, content, {
                              ...options,
                              waitForAck: true,
                            })""", {"to": to, "content": content, "options": options})
        self.logger.debug(f'{self.session}: Send Message {send_result=}')
        # result = await self.page_evaluate("""async (messageId) => {
        #                 return JSON.parse(JSON.stringify(await WAPI.getMessageById(messageId)));
        #               }""", send_result.get("id"))
        return send_result

    async def sendMessageOptions(self, chat, content, options=None):
        if not options:
            options = {}
        message_id = await self.page_evaluate("""({ chat, content, options }) => {
        return WAPI.sendMessageOptions(chat, content, options);
      }""", {"chat": chat, "content": content, "options": options})
        result = await self.page_evaluate("""(messageId) => WAPI.getMessageById(messageId)""", message_id)
        return result

    async def sendImage(self, to, filePath, filename="", caption="", quotedMessageId=None, isViewOnce=None):
        to = self.valid_chatId(to)
        if filePath and os.path.exists(filePath):
            _base64 = self.convert_to_base64(filePath)
            filename = os.path.basename(filePath) if not filename else filename
            return await self.sendImageFromBase64(to, _base64, filename, caption, quotedMessageId, isViewOnce)
        else:
            print("Path Not Found")

    async def sendImageFromBase64(self, to, _base64, filename, caption, quotedMessageId, isViewOnce):
        mime_type = self.base64MimeType(_base64)
        if not mime_type:
            print("Not valid mimeType")
            return
        if 'image' not in mime_type:
            print('Not an image, allowed formats png, jpeg and webp')
            return
        # filename = filenameFromMimeType(filename, mimeType)
        result = await self.page_evaluate("""async ({
        to,
        base64,
        filename,
        caption,
        quotedMessageId,
        isViewOnce,
      }) => {
        const result = await WPP.chat.sendFileMessage(to, base64, {
          type: 'image',
          isViewOnce,
          filename,
          caption,
          quotedMsg: quotedMessageId,
          waitForAck: true,
        }).catch((e) => {return e});
        
        return {
          ack: result.ack,
          id: result.id,
          sendMsgResult: await result.sendMsgResult,
          error: result.message,
        };
      }""", {"to": to, "base64": _base64, "filename": filename, "caption": caption, "quotedMessageId": quotedMessageId,
             "isViewOnce": isViewOnce})
        return result

    async def reply(self, to, content, quotedMsg):
        """

        :param to:
        :param content:
        :param quotedMsg: @param quotedMsg Message id to reply to.
        :return:
        """
        to = self.valid_chatId(to)
        result = await self.page_evaluate("""({ to, content, quotedMsg }) => {
                                    return WPP.chat.sendTextMessage(to, content, { quotedMsg });
                                  }""", {"to": to, "content": content, "quotedMsg": quotedMsg})
        message = await self.page_evaluate("(messageId: any) => WAPI.getMessageById(messageId)", result.get("id"))
        return message

    async def sendFile(self, to, pathOrBase64, nameOrOptions, caption):
        to = self.valid_chatId(to)
        options = {"type": 'auto-detect'}
        if type(nameOrOptions) is str:
            options["filename"] = nameOrOptions
            options["caption"] = caption

        elif type(nameOrOptions) is dict:
            options = nameOrOptions

        _base64 = ''
        if pathOrBase64.startswith('data:'):
            _base64 = pathOrBase64
        else:
            if pathOrBase64 and os.path.exists(pathOrBase64):
                _base64 = self.convert_to_base64(pathOrBase64)

            if not options.get("filename"):
                options["filename"] = os.path.basename(pathOrBase64)
        if not _base64:
            print("Empty or invalid file or base64")
            return

        return await self.page_evaluate("""async ({ to, base64, options }) => {
        const result = await WPP.chat.sendFileMessage(to, base64, options);
        return {
          ack: result.ack,
          id: result.id,
          sendMsgResult: await result.sendMsgResult,
        };
      }""", {"to": to, "base64": _base64, "options": options})

    async def sendContactVcard(self, to, contactsId, name):
        """
          /**
           * Sends contact card to iven chat id
           * @category Chat
           * @param to Chat id
           * @param contactsId Example: 0000@c.us | [000@c.us, 1111@c.us]
           */
        """
        to = self.valid_chatId(to)
        return await self.page_evaluate("""({ to, contactsId, name }) => {
        return WPP.chat.sendVCardContactMessage(to, {
          id: contactsId,
          name: name,
        });
      }""", {"to": to, "contactsId": contactsId, "name": name})

    async def forwardMessages(self, to, messages, skipMyMessages):
        to = self.valid_chatId(to)
        return await self.page_evaluate("""({ to, messages, skipMyMessages }) =>
        WAPI.forwardMessages(to, messages, skipMyMessages)""",
                                        {"to": to, "messages": messages, "skipMyMessages": skipMyMessages})

    async def sendLocation(self, to, options):
        to = self.valid_chatId(to)
        options = {
            "lat": options.get("latitude"),
            "lng": options.get("longitude"),
            "title": options.get("title"),
        }
        return await self.page_evaluate("""async ({ to, options }) => {
        const result = await WPP.chat.sendLocationMessage(to, options);

        return {
          ack: result.ack,
          id: result.id,
          sendMsgResult: await result.sendMsgResult,
        };
      }""", {"to": to, "options": options})

    async def sendSeen(self, chatId):
        chatId = self.valid_chatId(chatId)
        return await self.page_evaluate("(chatId) => WPP.chat.markIsRead(chatId)", chatId)

    async def startTyping(self, to, duration=None):
        to = self.valid_chatId(to)
        return await self.page_evaluate("({ to, duration }) => WPP.chat.markIsComposing(to, duration)",
                                        {"to": to, "duration": duration})

    async def stopTyping(self, to):
        to = self.valid_chatId(to)
        return await self.page_evaluate("(to) => WPP.chat.markIsPaused(to)", to)

    async def setOnlinePresence(self, online=True):
        return await self.page_evaluate("(online) => WPP.conn.markAvailable(online)", online)

    async def sendListMessage(self, to, options):
        to = self.valid_chatId(to)
        """
          /**
           * Sends a list message
           *
           * ```typescript
           *   // Example
           *   client.sendListMessage('<number>@c.us', {
           *     buttonText: 'Click here',
           *     description: 'Choose one option',
           *     sections: [
           *       {
           *         title: 'Section 1',
           *         rows: [
           *           {
           *             rowId: 'my_custom_id',
           *             title: 'Test 1',
           *             description: 'Description 1',
           *           },
           *           {
           *             rowId: '2',
           *             title: 'Test 2',
           *             description: 'Description 2',
           *           },
           *         ],
           *       },
           *     ],
           *   });
           * ```
           *
           * @category Chat
           */
        """
        sendResult = await self.page_evaluate("({ to, options }) => WPP.chat.sendListMessage(to, options)",
                                              {"to": to, "options": options})
        result = await self.page_evaluate("""async ({ messageId }) => {
                        return JSON.parse(JSON.stringify(await WAPI.getMessageById(messageId)));
                      }""", sendResult.get("id"))
        return result

    async def setChatState(self, chatId, chatState):
        """
          /**
           * Sets the chat state
           * Deprecated in favor of Use startTyping or startRecording functions
           * @category Chat
           * @param chatState   Typing = 0, Recording = 1, Paused = 2
           * @param chatId
           * @deprecated Deprecated in favor of Use startTyping or startRecording functions
           */
        """
        chatId = self.valid_chatId(chatId)
        return await self.page_evaluate("""({ chatState, chatId }) => {
                WAPI.sendChatstate(chatState, chatId);
              }""", {"chatState": chatState, "chatId": chatId})

    @staticmethod
    def convert_to_base64(path):
        mimetypes_add = {"webp": "image/webp"}
        # mime = magic.Magic(mime=True)
        # content_type = mime.from_file(path)
        content_type = mimetypes.guess_type(path)[0]
        if not content_type:
            content_type = mimetypes_add.get(path.split(".")[-1], None)
        # filename = os.path.basename(path)
        with open(path, "rb") as image_file:
            archive = base64.b64encode(image_file.read())
            archive = archive.decode("utf-8")

        return "data:" + content_type + ";base64," + archive

    @staticmethod
    def base64MimeType(encoded):
        result = encoded.split(";base64")[0].split(":")[-1]
        return result