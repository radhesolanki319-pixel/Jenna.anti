package ai.jenna.app.network;

public interface JennaCallback {
    void onSuccess(String result);
    void onError(Throwable t);
}
