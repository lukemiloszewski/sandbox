import datetime
import os

import win32com.client


def save_attachments(start_date, end_date, names, file_extensions, save_folder):
    """
    Save email attachments from emails received between start_date and end_date,
    where the recipient or CC includes any name from the provided list, and the
    attachment file type matches any of the provided extensions.

    :param start_date: Start date as a datetime object
    :param end_date: End date as a datetime object
    :param names: List of names to check in 'To' or 'CC' fields
    :param file_extensions: List of file extensions to check (e.g., ['pdf', 'xlsx'])
    :param save_folder: Folder path where attachments will be saved
    """

    outlook = win32com.client.Dispatch("Outlook.Application")
    namespace = outlook.GetNamespace("MAPI")

    inbox = namespace.GetDefaultFolder(6)

    items = inbox.Items
    items = items.Restrict(
        f"[ReceivedTime] >= '{start_date.strftime('%m/%d/%Y %H:%M %p')}' AND [ReceivedTime] <= '{end_date.strftime('%m/%d/%Y %H:%M %p')}'"
    )

    for item in items:
        if item.Class == 43:  # 43 is the constant for MailItem in Outlook
            if any(name in item.To for name in names) or any(name in item.CC for name in names):
                received_time = item.ReceivedTime.strftime("%Y-%m-%d_%H-%M-%S")

                for attachment in item.Attachments:
                    if any(attachment.FileName.lower().endswith(ext) for ext in file_extensions):
                        filename = f"{received_time}_{attachment.FileName}"
                        filepath = os.path.join(save_folder, filename)

                        attachment.SaveAsFile(filepath)

                print(f"Attachments saved for email: {item.Subject}")


if __name__ == "__main__":
    # output folder
    save_folder = "C:/Users/lmiloszewski/code/aaa/outlook"

    # date params
    end_date = datetime.datetime.now()
    start_date = end_date - datetime.timedelta(days=30)

    # inbox names
    names = ["Investment Analytics", "Luke Miloszewski"]

    # file extensions
    file_extensions = ["pdf", "xlsx"]

    save_attachments(start_date, end_date, names, file_extensions, save_folder)
