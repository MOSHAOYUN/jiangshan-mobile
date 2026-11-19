package org.jiangshan.mobile;

import android.app.Activity;
import android.content.ActivityNotFoundException;
import android.content.Intent;
import android.graphics.Color;
import android.net.Uri;
import android.os.Build;
import android.os.Bundle;
import android.view.Gravity;
import android.view.View;
import android.webkit.CookieManager;
import android.webkit.MimeTypeMap;
import android.webkit.WebChromeClient;
import android.webkit.WebResourceError;
import android.webkit.WebResourceRequest;
import android.webkit.WebResourceResponse;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.widget.Button;
import android.widget.FrameLayout;
import android.widget.LinearLayout;
import android.widget.ProgressBar;
import android.widget.TextView;
import android.widget.Toast;

import java.io.ByteArrayInputStream;
import java.io.IOException;
import java.io.InputStream;
import java.nio.charset.StandardCharsets;
import java.util.HashMap;
import java.util.Locale;
import java.util.Map;

/** Platform-only shell: no JavaScript bridge and no third-party runtime library. */
public final class MainActivity extends Activity {
    private static final String LOCAL_HOST = "appassets.androidplatform.net";
    private static final String ROOT = "/assets/web/";
    private static final String START_URL = "https://" + LOCAL_HOST + ROOT + "index.html";
    private WebView webView;
    private ProgressBar progress;
    private LinearLayout errorPanel;
    private TextView errorText;

    @Override public void onCreate(Bundle state) {
        super.onCreate(state);
        FrameLayout root = new FrameLayout(this);
        root.setBackgroundColor(Color.WHITE);
        root.setFitsSystemWindows(true);
        setContentView(root);

        progress = new ProgressBar(this);
        FrameLayout.LayoutParams spinner = new FrameLayout.LayoutParams(96, 96, Gravity.CENTER);
        root.addView(progress, spinner);
        errorPanel = new LinearLayout(this);
        errorPanel.setOrientation(LinearLayout.VERTICAL);
        errorPanel.setGravity(Gravity.CENTER);
        errorPanel.setPadding(40, 40, 40, 40);
        errorPanel.setBackgroundColor(Color.WHITE);
        errorText = new TextView(this);
        errorText.setTextColor(Color.DKGRAY);
        errorText.setTextSize(17);
        errorText.setGravity(Gravity.CENTER);
        errorPanel.addView(errorText);
        Button retry = new Button(this);
        retry.setText("重新加载");
        retry.setOnClickListener(view -> {
            if (webView == null) {
                recreate();
            } else {
                errorPanel.setVisibility(View.GONE);
                progress.setVisibility(View.VISIBLE);
                webView.loadUrl(START_URL);
            }
        });
        errorPanel.addView(retry);
        errorPanel.setVisibility(View.GONE);
        root.addView(errorPanel, new FrameLayout.LayoutParams(-1, -1));

        try {
            webView = new WebView(this);
            root.addView(webView, 0, new FrameLayout.LayoutParams(-1, -1));
            configureWebView();
            webView.loadUrl(START_URL);
        } catch (RuntimeException exception) {
            showError("无法启动系统 WebView。请安装或更新 Android System WebView / Chrome 后重试。");
        }
    }

    @SuppressWarnings("deprecation")
    private void configureWebView() {
        WebSettings settings = webView.getSettings();
        settings.setJavaScriptEnabled(true);
        settings.setDomStorageEnabled(true);
        settings.setAllowFileAccess(false);
        settings.setAllowContentAccess(false);
        settings.setAllowFileAccessFromFileURLs(false);
        settings.setAllowUniversalAccessFromFileURLs(false);
        settings.setMixedContentMode(WebSettings.MIXED_CONTENT_NEVER_ALLOW);
        settings.setJavaScriptCanOpenWindowsAutomatically(false);
        settings.setSupportMultipleWindows(false);
        settings.setGeolocationEnabled(false);
        settings.setMediaPlaybackRequiresUserGesture(true);
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            settings.setSafeBrowsingEnabled(true);
        }
        CookieManager.getInstance().setAcceptThirdPartyCookies(webView, false);
        WebView.setWebContentsDebuggingEnabled(false);
        webView.setWebChromeClient(new WebChromeClient());
        webView.setWebViewClient(new WebViewClient() {
            @Override public WebResourceResponse shouldInterceptRequest(WebView view, WebResourceRequest request) {
                Uri uri = request.getUrl();
                if (LOCAL_HOST.equalsIgnoreCase(uri.getHost())) {
                    return serveAsset(uri);
                }
                // Even navigation forms that skip shouldOverrideUrlLoading (e.g.
                // POST) cannot turn the embedded view into an external browser.
                if (request.isForMainFrame()) {
                    return response(403, "Forbidden", "External page blocked");
                }
                String scheme = uri.getScheme();
                if (!"https".equalsIgnoreCase(scheme) && !"http".equalsIgnoreCase(scheme)) {
                    return response(403, "Forbidden", "Resource scheme blocked");
                }
                return null;
            }

            @Override public boolean shouldOverrideUrlLoading(WebView view, WebResourceRequest request) {
                return handleNavigation(request.getUrl(), request.isForMainFrame());
            }

            @SuppressWarnings("deprecation")
            @Override public boolean shouldOverrideUrlLoading(WebView view, String url) {
                return handleNavigation(Uri.parse(url), true);
            }

            @Override public void onPageFinished(WebView view, String url) {
                progress.setVisibility(View.GONE);
            }

            @Override public void onReceivedError(WebView view, WebResourceRequest request, WebResourceError error) {
                if (request.isForMainFrame()) {
                    showError("页面加载失败，请重新加载。若问题持续，请确认手机版网页资源已完整打包。");
                }
            }

            @Override public void onReceivedHttpError(WebView view, WebResourceRequest request, WebResourceResponse error) {
                if (request.isForMainFrame()) {
                    showError("页面资源不可用（" + error.getStatusCode() + "）。请确认 assets/web/index.html 已打包。");
                }
            }
        });
    }

    private boolean isLocal(Uri uri) {
        return "https".equalsIgnoreCase(uri.getScheme())
                && LOCAL_HOST.equalsIgnoreCase(uri.getHost())
                && (uri.getPort() == -1 || uri.getPort() == 443)
                && uri.getUserInfo() == null;
    }

    private boolean handleNavigation(Uri uri, boolean mainFrame) {
        String path = uri.getPath();
        if (isLocal(uri)) {
            return path == null || !path.startsWith(ROOT) || !safePath(path);
        }
        String scheme = uri.getScheme();
        if (mainFrame && ("https".equalsIgnoreCase(scheme) || "http".equalsIgnoreCase(scheme))) {
            try {
                Intent intent = new Intent(Intent.ACTION_VIEW, uri);
                intent.addCategory(Intent.CATEGORY_BROWSABLE);
                startActivity(intent);
            } catch (ActivityNotFoundException | SecurityException exception) {
                Toast.makeText(this, "没有可打开此链接的浏览器", Toast.LENGTH_LONG).show();
            }
        } else if (mainFrame) {
            Toast.makeText(this, "已阻止不支持的链接类型", Toast.LENGTH_SHORT).show();
        }
        // Deny unsupported schemes delivered to this callback. WebView can execute
        // javascript: links inside the document without invoking this callback;
        // trusted page code must avoid them (see README).
        return true;
    }

    private boolean safePath(String path) {
        if (path.indexOf('\\') >= 0 || path.indexOf('\0') >= 0) return false;
        for (String segment : path.split("/")) {
            if ("..".equals(segment) || ".".equals(segment)) return false;
        }
        return true;
    }

    private WebResourceResponse serveAsset(Uri uri) {
        String path = uri.getPath(); // Android Uri decodes percent-encoded path segments.
        if (!isLocal(uri) || path == null || !path.startsWith(ROOT) || !safePath(path)) {
            return response(403, "Forbidden", "Asset path blocked");
        }
        String asset = "web/" + path.substring(ROOT.length());
        if (asset.endsWith("/")) asset += "index.html";
        try {
            InputStream stream = getAssets().open(asset);
            String extension = MimeTypeMap.getFileExtensionFromUrl(asset).toLowerCase(Locale.ROOT);
            String mime = MimeTypeMap.getSingleton().getMimeTypeFromExtension(extension);
            if ("js".equals(extension) || "mjs".equals(extension)) mime = "application/javascript";
            if ("json".equals(extension) || "geojson".equals(extension)) mime = "application/json";
            if ("wasm".equals(extension)) mime = "application/wasm";
            if ("pbf".equals(extension)) mime = "application/x-protobuf";
            if (mime == null) mime = "application/octet-stream";
            Map<String, String> headers = new HashMap<>();
            headers.put("Cache-Control", "no-cache");
            headers.put("X-Content-Type-Options", "nosniff");
            return new WebResourceResponse(mime, "UTF-8", 200, "OK", headers, stream);
        } catch (IOException exception) {
            return response(404, "Not Found", "Packaged asset not found");
        }
    }

    private WebResourceResponse response(int status, String reason, String text) {
        return new WebResourceResponse("text/plain", "UTF-8", status, reason, null,
                new ByteArrayInputStream(text.getBytes(StandardCharsets.UTF_8)));
    }

    private void showError(String message) {
        progress.setVisibility(View.GONE);
        errorText.setText(message);
        errorPanel.setVisibility(View.VISIBLE);
        errorPanel.bringToFront();
    }

    @SuppressWarnings("deprecation")
    @Override public void onBackPressed() {
        if (webView != null && webView.canGoBack()) {
            errorPanel.setVisibility(View.GONE);
            webView.goBack();
        } else {
            super.onBackPressed();
        }
    }

    @Override protected void onDestroy() {
        if (webView != null) {
            webView.stopLoading();
            webView.destroy();
            webView = null;
        }
        super.onDestroy();
    }
}
