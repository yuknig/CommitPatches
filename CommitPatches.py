import argparse
import os

def parse_commit_message_from_patch_file(patch_path):
    with open(patch_path, 'r') as patch_file:
        patch_text = patch_file.read()

    msg_start = patch_text.find('Subject:')
    msg_end = patch_text.find('---')
    if msg_start == -1 or msg_end == -1:
        return

    msg_start += len('Subject:')
    msg = patch_text[msg_start:msg_end]
    msg = msg.strip()
    if (msg.startswith('[PATCH]')):
        msg = msg[len('[PATCH]'):]
        msg = msg.strip()

    # leave double line breaks only
    lf_pos = 0
    while True:
        lf_pos = msg.find('\n', lf_pos)
        if lf_pos == -1:
            break;
        if lf_pos+1 < len(msg) and msg[lf_pos+1] != '\n':
            msg = msg[:lf_pos] + msg[lf_pos+1:]
        lf_pos += 1
    return msg


def process_dir_with_patches(dir):
    if not os.path.isdir(dir):
        raise NotADirectoryError('Wrong folder path passed:' + str(dir))

    dir_files = os.listdir(dir)
    if len(dir_files) == 0:
        print('No files found at' + str(dir))
        return

    commit_dir = os.path.join(dir, 'commit')
    if os.path.exists(commit_dir):
        print('Warning: path already exists: ' + commit_dir)
    else:
        os.mkdir(commit_dir)
    bat_file_path = os.path.join(commit_dir, 'commit.bat')
    if os.path.exists(bat_file_path):
        os.remove(bat_file_path)

    for file_idx, file in enumerate(dir_files):
        if not file.endswith('.patch'):
            continue

        patch_path = os.path.join(dir, file)
        msg = parse_commit_message_from_patch_file(patch_path)
        msg_file_name = '{0:03d}.msg'.format(file_idx+1)
        msg_file_path = os.path.join(commit_dir, msg_file_name)
        with open(msg_file_path, 'w') as msg_file:
            msg_file.write(msg)

        bat_lines = []
        bat_lines.append(':: apply commit #{} \'{}\'/b\n'.format(file_idx+1, file))
        bat_lines.append('svn patch \"{}\" || exit /b\n'.format(patch_path))
        bat_lines.append('svn commit -F \"{}\" || exit /b\n'.format(msg_file_path))
        bat_lines.append('\n')

        with open(bat_file_path, 'a') as bat_file:
            bat_file.writelines(bat_lines)


if __name__ == '__main__':
    arg_parse = argparse.ArgumentParser(description='Utility to automate commiting of patch set')
    arg_parse.add_argument('--path', help='folder with patch files')
    args = arg_parse.parse_args()

    process_dir_with_patches(args.path)
