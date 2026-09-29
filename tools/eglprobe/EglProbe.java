import android.opengl.EGL14;
import android.opengl.EGLConfig;
import android.opengl.EGLDisplay;

/**
 * Lists the EGL configs the Android guest exposes and reports whether
 * GLSurfaceView's ComponentSizeChooser would find a match for the requested
 * sizes (exact RGBA, at least the requested depth and stencil, GLES2-renderable).
 *
 * Runs without an APK: see scripts/egl_probe.sh.
 * Usage: EglProbe [r g b a depth stencil]   (default 5 6 5 0 16 8, cocos2d-x 2.x)
 */
public final class EglProbe {
    private static int attr(EGLDisplay display, EGLConfig config, int attribute) {
        int[] value = new int[1];
        EGL14.eglGetConfigAttrib(display, config, attribute, value, 0);
        return value[0];
    }

    public static void main(String[] args) {
        int[] want = {5, 6, 5, 0, 16, 8};
        if (args.length == 6) {
            for (int i = 0; i < 6; i++) want[i] = Integer.parseInt(args[i]);
        }

        EGLDisplay display = EGL14.eglGetDisplay(EGL14.EGL_DEFAULT_DISPLAY);
        int[] version = new int[2];
        if (!EGL14.eglInitialize(display, version, 0, version, 1)) {
            throw new IllegalStateException("eglInitialize failed: 0x" + Integer.toHexString(EGL14.eglGetError()));
        }
        System.out.println("EGL " + version[0] + "." + version[1] + " vendor=" + EGL14.eglQueryString(display, EGL14.EGL_VENDOR));

        int[] count = new int[1];
        EGL14.eglGetConfigs(display, null, 0, 0, count, 0);
        EGLConfig[] configs = new EGLConfig[count[0]];
        EGL14.eglGetConfigs(display, configs, 0, configs.length, count, 0);
        System.out.println("configs=" + count[0] + "  (id r g b a depth stencil samples surface renderable)");
        for (EGLConfig c : configs) {
            System.out.printf("  %3d  %d %d %d %d  %2d %d  %d  0x%x 0x%x%n",
                attr(display, c, EGL14.EGL_CONFIG_ID),
                attr(display, c, EGL14.EGL_RED_SIZE), attr(display, c, EGL14.EGL_GREEN_SIZE),
                attr(display, c, EGL14.EGL_BLUE_SIZE), attr(display, c, EGL14.EGL_ALPHA_SIZE),
                attr(display, c, EGL14.EGL_DEPTH_SIZE), attr(display, c, EGL14.EGL_STENCIL_SIZE),
                attr(display, c, EGL14.EGL_SAMPLES),
                attr(display, c, EGL14.EGL_SURFACE_TYPE), attr(display, c, EGL14.EGL_RENDERABLE_TYPE));
        }

        // Same spec GLSurfaceView builds for setEGLConfigChooser(r, g, b, a, depth, stencil)
        // with setEGLContextClientVersion(2).
        int[] spec = {
            EGL14.EGL_RED_SIZE, want[0], EGL14.EGL_GREEN_SIZE, want[1],
            EGL14.EGL_BLUE_SIZE, want[2], EGL14.EGL_ALPHA_SIZE, want[3],
            EGL14.EGL_DEPTH_SIZE, want[4], EGL14.EGL_STENCIL_SIZE, want[5],
            EGL14.EGL_RENDERABLE_TYPE, EGL14.EGL_OPENGL_ES2_BIT, EGL14.EGL_NONE,
        };
        EGL14.eglChooseConfig(display, spec, 0, null, 0, 0, count, 0);
        EGLConfig[] candidates = new EGLConfig[Math.max(count[0], 1)];
        EGL14.eglChooseConfig(display, spec, 0, candidates, 0, candidates.length, count, 0);
        int matchId = -1;
        for (int i = 0; i < count[0] && matchId < 0; i++) {
            EGLConfig c = candidates[i];
            if (attr(display, c, EGL14.EGL_DEPTH_SIZE) >= want[4]
                && attr(display, c, EGL14.EGL_STENCIL_SIZE) >= want[5]
                && attr(display, c, EGL14.EGL_RED_SIZE) == want[0]
                && attr(display, c, EGL14.EGL_GREEN_SIZE) == want[1]
                && attr(display, c, EGL14.EGL_BLUE_SIZE) == want[2]
                && attr(display, c, EGL14.EGL_ALPHA_SIZE) == want[3]) {
                matchId = attr(display, c, EGL14.EGL_CONFIG_ID);
            }
        }
        System.out.printf("request r%d g%d b%d a%d d%d s%d: eglChooseConfig candidates=%d -> %s%n",
            want[0], want[1], want[2], want[3], want[4], want[5], count[0],
            matchId >= 0 ? "MATCH config " + matchId : "NO MATCH (GLSurfaceView would throw 'No config chosen')");
        EGL14.eglTerminate(display);
    }
}
