"""MeetingSplit native application / console-free portable readiness probe."""
import sys

if __name__ == '__main__':
    if '--self-check' in sys.argv:
        from desktop.self_check import main as check_main
        pos=sys.argv.index('--self-check')
        output_path=sys.argv[pos+1] if len(sys.argv)>pos+1 and not sys.argv[pos+1].startswith('--') else None
        raise SystemExit(check_main(output_path))
    from desktop.main import main
    main()
