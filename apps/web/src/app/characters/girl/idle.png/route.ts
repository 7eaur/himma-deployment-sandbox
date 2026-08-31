export function GET(request: Request) {
  return Response.redirect(new URL("/characters/girl/welcome.png", request.url), 307);
}
