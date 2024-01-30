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

    # Remove unneeded line break
    end_pos = msg.find('\n\n') # process to first double line break
    if end_pos == -1:
        end_pos = len(msg)
    lf_pos = 0
    while lf_pos <= end_pos:
        lf_pos = msg.find('\n', lf_pos)
        if lf_pos == -1:
            break;
        if lf_pos+1 < len(msg) and msg[lf_pos+1] != '\n':
            msg = msg[:lf_pos] + msg[lf_pos+1:]
        lf_pos += 1
    return msg


def parse_patch_num(patch_file_name):
    patch_num = 0
    for ch in patch_file_name:
        digit = ord(ch) - ord('0')
        if digit < 0 or digit > 9:
            break
        patch_num = digit + patch_num*10
    return patch_num

# return sorted list of items: { patch_num : patch_file_name }
def get_patch_dict(patch_dir):
    dir_files = os.listdir(patch_dir)

    dict = {}
    for file_idx, file_name in enumerate(dir_files):
        if not file_name.endswith('.patch'):
            continue

        # extract patch number
        num = parse_patch_num(file_name)
        dict[num] = file_name

    sdict = sorted(dict.items())
    first_patch_num = sdict[0][0];
    last_patch_num = sdict[-1][0]

    if len(sdict) != (last_patch_num-first_patch_num+1):
        print('Patch list seems to be incomplete')
        raise RuntimeError('Missing patches in set')

    return sdict

def process_dir_with_patches(dir):
    if not os.path.isdir(dir):
        raise NotADirectoryError('Wrong folder path passed:' + str(dir))

    patch_dict = get_patch_dict(dir)
    if len(patch_dict) == 0:
        print('No files found at' + str(dir))
        return

    commit_dir = os.path.join(dir, 'commit')
    if os.path.exists(commit_dir):
        print('Warning: path already exists: ' + commit_dir)
    else:
        os.mkdir(commit_dir)
    bat_file_path = os.path.join(commit_dir, 'commit.bat')
    if os.path.exists(bat_file_path):
        print('Warning: rewriting commit.bat')
        os.remove(bat_file_path)

    # write bat file head
    with open(bat_file_path, 'a') as bat_file:
        bat_file.writelines(["svn revert -R .\n", "svn up\n\n"])

    # iterate files
    for patch_num, patch_file_name in patch_dict:

        patch_path = os.path.join(dir, patch_file_name)
        msg = parse_commit_message_from_patch_file(patch_path)
        msg_file_name = '{0:03d}.msg'.format(patch_num)
        msg_file_path = os.path.join(commit_dir, msg_file_name)
        with open(msg_file_path, 'w') as msg_file:
            msg_file.write(msg)

        bat_lines = []
        bat_lines.append(':: apply patch #{} \'{}\'\n'.format(patch_num, patch_file_name))
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
