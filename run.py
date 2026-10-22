"""MeetingSplit native application / console-free portable readiness probe."""
import sys

if __name__ == '__main__':
    if '--ui-qa' in sys.argv:
        from desktop.ui_qa import main as ui_qa_main
        raise SystemExit(ui_qa_main(sys.argv[sys.argv.index('--ui-qa')+1]))
    if '--hardware-qa' in sys.argv:
        from desktop.hardware_qa import main as hardware_main
        pos=sys.argv.index('--hardware-qa')
        raise SystemExit(hardware_main(*sys.argv[pos+1:pos+3]))
    if '--cuda-probe' in sys.argv:
        raise SystemExit('CUDA probe disabled. This CPU-only build never initializes NVIDIA GPU.')
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
