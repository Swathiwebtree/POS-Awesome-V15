import { defineConfig } from "vite";
import vue from "@vitejs/plugin-vue";
// IMPORTANT: Use 'path' for the resolve function, not 'resolve' from 'path' directly.
// The standard 'path.resolve' function is required here.
import path, { resolve } from "path"; 
import frappeVueStyle from "../frappe-vue-style";
import { viteStaticCopy } from "vite-plugin-static-copy";
import tailwindcss from "tailwindcss";
import autoprefixer from "autoprefixer";

export default defineConfig({
    plugins: [
        frappeVueStyle(),
        vue(),
        viteStaticCopy({
            targets: [
                {
                    src: "src/posapp/workers",
                    dest: "posapp",
                },
                {
                    src: "src/libs/*",
                    dest: "libs",
                },
                {
                    src: "src/offline/*",
                    dest: "offline",
                },
            ],
        }),
    ],
    css: {
        postcss: {
            plugins: [tailwindcss(), autoprefixer()],
        },
    },
    build: {
        target: "esnext",
        lib: {
            entry: resolve(__dirname, "src/posawesome.bundle.js"),
            name: "PosAwesome",
            fileName: "posawesome",
        },
        outDir: "../posawesome/public/dist/js",
        emptyOutDir: true,
        rollupOptions: {
            external: ["socket.io-client"],
            output: [
                {
                    format: "es",
                    entryFileNames: "posawesome.js",
                },
                {
                    format: "umd",
                    name: "PosAwesome",
                    entryFileNames: "posawesome.umd.js",
                    globals: {
                        "socket.io-client": "io",
                    },
                },
            ],
        },
    },
    // 💡 FIX APPLIED HERE
    resolve: {
        alias: {
            // Your existing alias
            "@": resolve(__dirname, "src"),
            
            // **CRITICAL FIX:** Alias to resolve "frappe-pos/src/..." imports.
            // This navigates from:
            // frontend/ -> posawesome/ -> apps/ -> frappe_pos/ -> public/ -> src/
            'frappe-pos/src': path.resolve(
                __dirname,
                '..', // back to posawesome/
                '..', // back to apps/
                'frappe_pos', // into the frappe_pos app folder
                'public',
                'src'
            ),
        },
    },
    define: {
        "process.env.NODE_ENV": '"production"',
        process: '{"env":{}}',
    },
});