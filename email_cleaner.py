import imaplib
import sys
from dotenv import load_dotenv
import os
import email
from email.header import decode_header
from email.utils import parsedate_to_datetime

def decode_mime_words(s):
    decoded_words = decode_header(s)
    return ''.join([str(t[0], t[1] or 'utf-8') if isinstance(t[0], bytes) else t[0] for t in decoded_words])

def delete_emails(sender_emails, server_address, username, password):
    try:
        # 连接到IMAP服务器
        mail = imaplib.IMAP4_SSL(server_address)
        
        # 登录邮箱
        print("正在登录...")
        mail.login(username, password)
        
        # 选择收件箱文件夹
        mail.select('inbox')
        
        for sender_email in sender_emails:
            # 使用UID搜索来自指定发件人的邮件
            print(f"正在搜索来自 {sender_email} 的邮件...")
            status, data = mail.uid('search', None, f'(FROM "{sender_email}")')
            if status == 'OK':
                email_ids = data[0].split()
                
                if not email_ids:
                    print(f"没有找到要删除的邮件。发件人: {sender_email}")
                    continue
                
                # 转换email_ids为字符串列表
                email_ids = [eid.decode('utf-8') for eid in email_ids]
                
                print(f"准备删除 {len(email_ids)} 封邮件...")
                for email_id in email_ids:
                    # 获取邮件信息（可选）
                    status, msg_data = mail.uid('fetch', email_id, '(RFC822)')
                    if status == 'OK':
                        msg = email.message_from_bytes(msg_data[0][1])
                        subject = decode_mime_words(msg.get('Subject', ''))
                        date = parsedate_to_datetime(msg.get('Date', ''))
                        from_email = decode_mime_words(msg.get('From', ''))
                        to_email = decode_mime_words(msg.get('To', ''))
                        print(f"删除邮件: {date} - {subject} - 发件人: {from_email} - 收件人: {to_email}")
                    
                    # 使用UID标记邮件为删除
                    mail.uid('STORE', email_id, '+FLAGS', '\\Deleted')
                    print(f"已标记邮件UID {email_id} 为删除")
                
                # 立即执行删除操作
                mail.expunge()
                print("删除成功！")
            else:
                print(f"搜索失败。发件人: {sender_email}")
            
    except Exception as e:
        print(f"错误: {e}")
    finally:
        # 断开连接
        mail.logout()

if __name__ == "__main__":
    try:
        # 加载环境变量
        load_dotenv()
        
        # 获取配置
        email_sets = []
        set_index = 1
        while True:
            server_address = os.getenv(f"EMAIL_SET_{set_index}_SERVER_ADDRESS")
            username = os.getenv(f"EMAIL_SET_{set_index}_USERNAME")
            password = os.getenv(f"EMAIL_SET_{set_index}_PASSWORD")
            sender_emails_file = os.getenv(f"EMAIL_SET_{set_index}_SENDER_EMAILS_FILE")
            
            if not server_address or not username or not password or not sender_emails_file:
                break
            
            with open(sender_emails_file, 'r') as file:
                sender_emails = [line.strip() for line in file.readlines()]
            
            email_sets.append({
                "sender_emails": sender_emails,
                "server_address": server_address,
                "username": username,
                "password": password
            })
            
            set_index += 1
        
        # 处理每个配置
        for email_set in email_sets:
            delete_emails(email_set["sender_emails"], email_set["server_address"], email_set["username"], email_set["password"])
    except KeyboardInterrupt:
        print("\n程序已中断。")
    except EOFError:
        print("\n输入结束，程序退出。")