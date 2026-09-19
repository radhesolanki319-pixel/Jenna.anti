package ai.jenna.app.terminal;

import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;

public class ShellExecutor {

    public static String execute(String command) {
        StringBuilder output = new StringBuilder();
        try {
            Process process = Runtime.getRuntime().exec(new String[]{"/system/bin/sh", "-c", command});
            BufferedReader reader = new BufferedReader(new InputStreamReader(process.getInputStream(), StandardCharsets.UTF_8));
            BufferedReader errorReader = new BufferedReader(new InputStreamReader(process.getErrorStream(), StandardCharsets.UTF_8));

            String line;
            while ((line = reader.readLine()) != null) {
                output.append(line).append("\n");
            }
            while ((line = errorReader.readLine()) != null) {
                output.append("[stderr] ").append(line).append("\n");
            }

            process.waitFor();
            reader.close();
            errorReader.close();
        } catch (Exception e) {
            return "Execution error: " + e.getMessage();
        }

        String res = output.toString().trim();
        return res.isEmpty() ? "Command executed successfully (no output)." : res;
    }
}
