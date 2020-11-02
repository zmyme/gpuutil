from gpuutil import GPUStat
import sys

if __name__ == '__main__':
    stat = GPUStat()
    show_types = ['brief', 'detail']
    default_type = 'brief'
    show_type = default_type
    if len(sys.argv) > 1:
        show_type = str(sys.argv[1])
    if show_type in show_types:
        stat.show(disp_type=show_type)
    else:
        print('The given type is \"{0}\" not understood, and it should be choosen from {1}\nUsing default type \"{2}\".'.format(show_type, show_types, default_type))
        show_type = default_type
        stat.show(disp_type=show_type)

    # auto_set(1, ask=True, blacklist=[], show=True)