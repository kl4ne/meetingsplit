"""MeetingSplit native application / console-free portable readiness probe."""
import sys

if __name__ == '__main__':
    if '--cuda-probe' in sys.argv:
        from desktop.cuda_probe import child
        pos=sys.argv.index('--cuda-probe')
        raise SystemExit(child(*sys.argv[pos+1:pos+4]))
    if '--configure-components' in sys.argv:
        from desktop.component_setup import main as component_main
        raise SystemExit(component_main())
    if '--self-check' in sys.argv:
        from desktop.self_check import main as check_main
        pos=sys.argv.index('--self-check')
        output_path=sys.argv[pos+1] if len(sys.argv)>pos+1 and not sys.argv[pos+1].startswith('--') else None
        raise SystemExit(check_main(output_path))
    from desktop.main import main
    main()
