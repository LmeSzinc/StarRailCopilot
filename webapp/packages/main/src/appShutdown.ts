type StopBackend = () => Promise<void>;
type QuitElectron = () => void;
type ReportError = (error: unknown) => void;

export class ShutdownCoordinator {
  private shutdownPromise: Promise<void> | null = null;
  private canQuit = false;

  constructor(
    private readonly stopBackend: StopBackend,
    private readonly quitElectron: QuitElectron,
    private readonly reportError: ReportError = () => undefined,
  ) {}

  get readyToQuit() {
    return this.canQuit;
  }

  request(): Promise<void> {
    if (this.shutdownPromise) return this.shutdownPromise;

    this.shutdownPromise = (async () => {
      try {
        await this.stopBackend();
      } catch (error) {
        this.reportError(error);
      }

      this.canQuit = true;
      this.quitElectron();
    })();

    return this.shutdownPromise;
  }
}
