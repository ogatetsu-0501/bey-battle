import com.sun.net.httpserver.Headers;
import com.sun.net.httpserver.HttpExchange;
import com.sun.net.httpserver.HttpHandler;
import com.sun.net.httpserver.HttpServer;

import java.io.IOException;
import java.io.OutputStream;
import java.net.InetSocketAddress;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;

public class PartsApiServer {
    private static final String DEFAULT_HOST = "0.0.0.0";
    private static final int DEFAULT_PORT = 8080;
    private static final Path PARTS_JSON_PATH = Path.of("../data/parts.json");

    // --- main ----------------------------------------------------------------------
    //【呼ばれる場面】Javaプロセスを起動した直後にJVMエントリーポイントとして呼ばれる。
    //【すること】起動引数から待受ホストとポートを解釈し、パーツJSON返却APIとCORSプリフライト応答を登録して待受を開始する。
    //【入力】args（起動引数（String[]））
    //【出力】なし（void）
    //【外部境界】HTTP待受（HttpServer）、標準出力（System.out）
    // -------------------------------------------------------------------------------
    public static void main(String[] args) throws IOException {
        String host = args.length > 0 ? args[0] : DEFAULT_HOST;
        int port = args.length > 1 ? Integer.parseInt(args[1]) : DEFAULT_PORT;

        HttpServer server = HttpServer.create(new InetSocketAddress(host, port), 0);
        server.createContext("/api/parts", new PartsHandler());
        server.setExecutor(null);
        server.start();
        System.out.println("Parts API server started at http://" + host + ":" + port + "/api/parts");
    }

    private static class PartsHandler implements HttpHandler {
        // --- handle --------------------------------------------------------------------
        //【呼ばれる場面】/api/parts へのHTTPアクセスを受けた都度、HTTPサーバーから呼ばれる。
        //【すること】OPTIONSはプリフライト応答だけ返し、それ以外はJSONファイルを読み込んで本文へ書き込み、失敗時は500を返す。
        //【入力】exchange（HTTPリクエスト/レスポンスコンテキスト（HttpExchange））
        //【出力】なし（void）
        //【外部境界】ファイル読み込み（Files.readString）、HTTPレスポンス書き込み（HttpExchange）
        // -------------------------------------------------------------------------------
        public void handle(HttpExchange exchange) throws IOException {
            addCorsHeaders(exchange.getResponseHeaders());

            if ("OPTIONS".equalsIgnoreCase(exchange.getRequestMethod())) {
                exchange.sendResponseHeaders(204, -1);
                return;
            }

            try {
                String body = Files.readString(PARTS_JSON_PATH, StandardCharsets.UTF_8);
                byte[] bodyBytes = body.getBytes(StandardCharsets.UTF_8);
                exchange.getResponseHeaders().add("Content-Type", "application/json; charset=utf-8");
                exchange.sendResponseHeaders(200, bodyBytes.length);
                try (OutputStream outputStream = exchange.getResponseBody()) {
                    outputStream.write(bodyBytes);
                }
            } catch (IOException error) {
                String message = "{\"error\":\"failed to read parts json\"}";
                byte[] bodyBytes = message.getBytes(StandardCharsets.UTF_8);
                exchange.getResponseHeaders().add("Content-Type", "application/json; charset=utf-8");
                exchange.sendResponseHeaders(500, bodyBytes.length);
                try (OutputStream outputStream = exchange.getResponseBody()) {
                    outputStream.write(bodyBytes);
                }
            }
        }

        // --- addCorsHeaders -------------------------------------------------------------
        //【呼ばれる場面】各レスポンスを返す前に、ブラウザからのクロスオリジンアクセスを許可するときに呼ばれる。
        //【すること】必要なCORSヘッダーをまとめて付与し、React開発サーバーからの取得をブロックされない状態にする。
        //【入力】headers（HTTPレスポンスヘッダー（Headers））
        //【出力】なし（void）
        //【外部境界】HTTPレスポンスヘッダー
        // -------------------------------------------------------------------------------
        private void addCorsHeaders(Headers headers) {
            headers.add("Access-Control-Allow-Origin", "*");
            headers.add("Access-Control-Allow-Methods", "GET, OPTIONS");
            headers.add("Access-Control-Allow-Headers", "Content-Type");
        }
    }
}
