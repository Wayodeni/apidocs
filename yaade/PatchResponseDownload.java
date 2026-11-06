package com.espero.yaade.services;

import io.vertx.core.buffer.Buffer;
import io.vertx.core.json.JsonObject;
import io.vertx.ext.web.client.HttpResponse;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.Base64;
import jdk.internal.org.objectweb.asm.ClassReader;
import jdk.internal.org.objectweb.asm.ClassVisitor;
import jdk.internal.org.objectweb.asm.ClassWriter;
import jdk.internal.org.objectweb.asm.MethodVisitor;
import static jdk.internal.org.objectweb.asm.Opcodes.*;

public final class PatchResponseDownload {
    private static final String HTTP_RESPONSE = "io/vertx/ext/web/client/HttpResponse";
    private static final String JSON_OBJECT = "io/vertx/core/json/JsonObject";

    public static void main(String[] args) throws Exception {
        Path path = Path.of(args[0], "com/espero/yaade/services/RequestSender.class");
        ClassReader reader = new ClassReader(Files.readAllBytes(path));
        ClassWriter writer = new ClassWriter(reader, ClassWriter.COMPUTE_MAXS);
        int[] bodyReads = {0};
        reader.accept(new ClassVisitor(ASM8, writer) {
            @Override
            public MethodVisitor visitMethod(
                    int access, String name, String descriptor, String signature, String[] exceptions) {
                MethodVisitor method = super.visitMethod(access, name, descriptor, signature, exceptions);
                if (!name.equals("send")) {
                    return method;
                }
                return new MethodVisitor(ASM8, method) {
                    @Override
                    public void visitMethodInsn(
                            int opcode, String owner, String name, String descriptor, boolean isInterface) {
                        if (opcode == INVOKEINTERFACE && owner.equals(HTTP_RESPONSE)
                                && name.equals("bodyAsString") && descriptor.equals("()Ljava/lang/String;")
                                && bodyReads[0]++ == 0) {
                            // The first read has the result object, the "body" key and the response on the stack.
                            // Keep the result and key for put(), and pass the response and result to capture().
                            super.visitInsn(DUP2_X1);
                            super.visitInsn(POP2);
                            super.visitInsn(DUP_X2);
                            super.visitMethodInsn(INVOKESTATIC, "com/espero/yaade/services/ResponseDownload",
                                    "capture", "(L" + HTTP_RESPONSE + ";L" + JSON_OBJECT + ";)Ljava/lang/String;",
                                    false);
                            return;
                        }
                        super.visitMethodInsn(opcode, owner, name, descriptor, isInterface);
                    }
                };
            }
        }, 0);
        if (bodyReads[0] != 3) {
            throw new IllegalStateException("Unexpected response body reads in Yaade RequestSender");
        }
        Files.write(path, writer.toByteArray());
    }
}

final class ResponseDownload {
    static String capture(HttpResponse<?> response, JsonObject result) {
        Buffer body = response.bodyAsBuffer();
        if (body != null && body.length() > 0) {
            result.put("bodyBase64", Base64.getEncoder().encodeToString(body.getBytes()));
        }
        return response.bodyAsString();
    }
}
