import Image from "next/image";


export function ResearchFigure({
  src,
  alt,
  title,
  caption,
}: {
  src: string;
  alt: string;
  title: string;
  caption: string;
}) {
  return (
    <figure className="overflow-hidden rounded-2xl border border-zinc-800 bg-zinc-900">
      <div className="border-b border-zinc-800 p-5">
        <h3 className="font-semibold">
          {title}
        </h3>
      </div>

      <div className="bg-white p-3">
        <Image
          src={src}
          alt={alt}
          width={1400}
          height={900}
          className="h-auto w-full"
        />
      </div>

      <figcaption className="p-5 text-sm leading-6 text-zinc-400">
        {caption}
      </figcaption>
    </figure>
  );
}